import sys
import signal
import logging
from csn import parse, run_ibd, HelpMsg


def setup_logging(cfg):
    """Configure logging with appropriate level and format."""
    log_level = logging.DEBUG if getattr(cfg, "debug", False) else logging.INFO
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


def main():
    try:
        # Parse command-line arguments
        cfg = parse(sys.argv[1:])

        # Setup logging
        setup_logging(cfg)
        logging.info("Starting CSN client...")

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
    except Exception as e:
        logging.error(f"An error occurred during IBD process: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logging.info("CSN client shutting down")


if __name__ == "__main__":
    main()
