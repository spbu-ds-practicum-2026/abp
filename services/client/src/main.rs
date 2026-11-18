
/*
pm-wallet --help
syntax: pm-wallet <command> [params]
avaliable commands:
- create_wallet <filepath> -> public_key / error
filepath - path to a private key being created
returns wallet public id
- get_balance -> amount / error
returns wallet amount or error
- get_public_key -> public_key / error
returns wallet public key
- send <public_key> <amount> -> txId / error
public_key - recipient public key
amount - amount to send
returns transaction id or error
- status <txid> -> transaction_status (enum)
txid - transaction id to check status
returns status of transaction
*/


use clap::{Parser, Subcommand};
use std::path::PathBuf;
use std::error::Error;

pub mod pmwallet_proto {
    tonic::include_proto!("pmwallet.v1");
}

use tonic::transport::Channel;
use pmwallet_proto::node_service_client::NodeServiceClient;
use pmwallet_proto::*;

#[derive(Debug, Parser)]
#[command(
    name = "pm-wallet",
    about = "Command line interface for pm-wallet",
    arg_required_else_help = true,
    subcommand_required(true),
    subcommand_value_name = "command"
)]
struct Cli {
    #[arg(long = "node", value_name = "endpoint", required = true)]
    node_endpoint: String,

    #[command(subcommand)]
    command: Command,
}

#[derive(Debug, Subcommand)]
#[command(rename_all = "snake_case")]
enum Command {
    /// Create a new wallet and return its public key
    CreateWallet {
        /// Path to the file where the private key will be stored
        #[arg(value_name = "filepath")]
        filepath: PathBuf,
    },

    /// Get the current wallet balance
    GetBalance,

    /// Get the wallet's public key
    GetPublicKey,

    /// Send coins to another wallet and return the transaction ID
    Send {
        /// Recipient's public key
        #[arg(value_name = "public_key")]
        public_key: String,

        /// Amount of coins to send
        #[arg(value_name = "amount")]
        amount: u64,
    },

    /// Get the status of a transaction
    Status {
        /// Transaction ID to check
        #[arg(value_name = "txid")]
        txid: String,
    },
}

async fn create_node_connection(
    endpoint: String
) -> Result<NodeServiceClient<Channel>, tonic::transport::Error> {
    NodeServiceClient::connect(endpoint).await
}

async fn handle_command(mut service: NodeServiceClient<Channel>, command: Command) -> Result<(), Box<dyn Error>> {
    match command {
        Command::CreateWallet { filepath } => {
            println!("Creating wallet: {}", filepath.display());
        }

        Command::GetBalance => {
            let res = service.get_balance(
                GetBalanceRequest {
                    address: vec!(123)
                }
            ).await?.into_inner();
            println!("balance: {}", res.balance);
        }

        Command::GetPublicKey => {
            println!("Getting public key");
        }

        Command::Send { public_key, amount } => {
            let prep_tx_res = service.prepare_transaction(
                PrepareTransactionRequest {
                    sender_public_key: vec!(0),
                    recipient_address: vec!(0),
                    amount
                }
            ).await?.into_inner();
            
            let subm_tx_res = service.submit_transaction(
                SubmitTransactionRequest {
                    signed_transaction: vec!(0)
                }
            ).await?.into_inner();

            println!("{}", subm_tx_res.tx_id);
        }

        Command::Status { txid  } => {
            let res = service.get_transaction_status(
                GetTransactionStatusRequest {
                    tx_id: txid
                }
            ).await?.into_inner();
            println!("tx status: {}, tx confirmations: {}", res.status, res.confirmations);
        }
    }
    
    Ok(())
}


#[tokio::main]
async fn main() {
    let cli = Cli::parse();
    let mut client = match create_node_connection(cli.node_endpoint.clone()).await {
        Ok(client) => client,
        Err(err) => {
            eprintln!(
                "Error: could not connect to node at {}: {err}",
                cli.node_endpoint
            );
            std::process::exit(1);
        }
    };

    handle_command(client, cli.command)
        .await
        .unwrap_or_else(|err| eprintln!("error {}", err));
}

