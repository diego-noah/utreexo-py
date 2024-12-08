import sys
import signal
from csn import parse, run_ibd, HelpMsg

def handle_int_sig(signal_received, frame, sig, cfg):
    """Handle OS signals and notify to terminate gracefully."""
    sig.append(True)

def main():
    try:
        # Parse command-line arguments
        cfg = parse(sys.argv[1:])
    except Exception as e:
        print(e)
        print(HelpMsg)
        sys.exit(1)

    # Channel to signal graceful shutdown
    sig = []

    # Register signal handlers for SIGINT, SIGTERM, and SIGQUIT
    signal.signal(signal.SIGINT, lambda s, f: handle_int_sig(s, f, sig, cfg))
    signal.signal(signal.SIGTERM, lambda s, f: handle_int_sig(s, f, sig, cfg))
    signal.signal(signal.SIGQUIT, lambda s, f: handle_int_sig(s, f, sig, cfg))

    try:
        # Run IBD process
        run_ibd(cfg, sig)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

