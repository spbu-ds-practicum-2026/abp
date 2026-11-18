fn main() -> Result<(), Box<dyn std::error::Error>> {
    let proto = "../../proto/pmwallet/v1/node.proto";

    println!("cargo:rerun-if-changed={proto}");

    tonic_prost_build::compile_protos(proto)?;

    Ok(())
}
