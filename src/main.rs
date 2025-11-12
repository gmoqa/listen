mod cli;
mod audio;
mod config;
mod transcribe;
mod error;

use clap::Parser;
use anyhow::Result;

#[tokio::main]
async fn main() -> Result<()> {
    let args = cli::Args::parse();

    // Configure based on args
    let config = config::Config::from_args(&args)?;

    if args.verbose {
        println!("[DEBUG] Configuration: {:?}", config);
    }

    // Execute based on mode
    match args.file {
        Some(file_path) => {
            // File transcription mode
            transcribe::transcribe_file(&file_path, &config).await?;
        }
        None => {
            // Microphone recording mode
            audio::record_and_transcribe(&config).await?;
        }
    }

    Ok(())
}
