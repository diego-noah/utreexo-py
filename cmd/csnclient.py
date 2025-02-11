import sys
import signal
import logging
from csn import parse, run_ibd, HelpMsg


def setup_logging(cfg):
    """Configure logging with appropriate level and format."""
    log_level = logging.DEBUG if getattr(cfg, "debug", False) else logging.INFO

    # Add file handler if log_file is specified in config
    if hasattr(cfg, "log_file"):
        handlers = [logging.FileHandler(cfg.log_file), logging.StreamHandler()]
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            handlers=handlers,
        )
    else:
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )


def handle_int_sig(signal_received, frame, sig, cfg):
    """Handle OS signals and notify to terminate gracefully."""
    signal_name = signal.Signals(signal_received).name
    logging.info(f"Received {signal_name} signal. Initiating graceful shutdown...")
    sig.append(True)


def validate_config(cfg):
    """Validate the configuration parameters."""
    required_fields = ["host", "port"]  # Add required fields here
    missing_fields = [field for field in required_fields if not hasattr(cfg, field)]

    if missing_fields:
        raise ValueError(
            f"Missing required configuration fields: {', '.join(missing_fields)}"
        )

    if hasattr(cfg, "port"):
        if not isinstance(cfg.port, int) or cfg.port < 1 or cfg.port > 65535:
            raise ValueError("Port must be an integer between 1 and 65535")


def main():
    try:
        # Parse command-line arguments
        cfg = parse(sys.argv[1:])

        # Validate configuration
        validate_config(cfg)

        # Setup logging
        setup_logging(cfg)
        logging.info("Starting CSN client...")
        logging.debug(f"Configuration: {vars(cfg)}")

    except Exception as e:
        print(f"Configuration error: {e}")
        print(HelpMsg)
        sys.exit(1)

    # Channel to signal graceful shutdown
    sig = []

    # Register signal handlers for SIGINT, SIGTERM, and SIGQUIT
    signals = [signal.SIGINT, signal.SIGTERM, signal.SIGQUIT]
    for sig_type in signals:
        signal.signal(sig_type, lambda s, f: handle_int_sig(s, f, sig, cfg))

    logging.info("Signal handlers registered")

    try:
        # Run IBD process
        logging.info("Starting IBD process...")
        run_ibd(cfg, sig)
        logging.info("IBD process completed successfully")

    except KeyboardInterrupt:
        logging.info("Process interrupted by user")
        sys.exit(0)
    except ConnectionError as e:
        logging.error(f"Connection error: {e}")
        sys.exit(2)
    except Exception as e:
        logging.error(f"An error occurred during IBD process: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logging.info("CSN client shutting down")
        logging.shutdown()


if __name__ == "__main__":
    main()
