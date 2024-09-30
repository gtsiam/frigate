import argparse
import faulthandler
import multiprocessing as mp
import signal
import sys
import threading

from pydantic import ValidationError

from frigate import FrigateApp, FrigateConfig
from frigate.log import setup_logging


def main() -> None:
    # Show more information on python interpreter crash
    faulthandler.enable()

    # Switch multiprocessing start method to forkserver (the default as of python 3.14).
    # This must happen before anything else, or it's likely to segfault (ask me how I know).
    mp.set_start_method("forkserver", force=True)
    mp.set_forkserver_preload(["frigate"])

    # Start and configure the logging thread
    setup_logging()

    threading.current_thread().name = "frigate"

    # Make sure we exit cleanly on SIGTERM.
    signal.signal(signal.SIGTERM, lambda sig, frame: sys.exit())

    # Parse the cli arguments.
    parser = argparse.ArgumentParser(
        prog="Frigate",
        description="An NVR with realtime local object detection for IP cameras.",
    )
    parser.add_argument("--validate-config", action="store_true")
    args = parser.parse_args()

    # Load the configuration.
    try:
        config = FrigateConfig.load(install=True)
    except ValidationError as e:
        print("*************************************************************")
        print("*************************************************************")
        print("***    Your config file is not valid!                     ***")
        print("***    Please check the docs at                           ***")
        print("***    https://docs.frigate.video/configuration/          ***")
        print("*************************************************************")
        print("*************************************************************")
        print("***    Config Validation Errors                           ***")
        print("*************************************************************")
        for error in e.errors():
            location = ".".join(str(item) for item in error["loc"])
            print(f"{location}: {error['msg']}")
        print("*************************************************************")
        print("***    End Config Validation Errors                       ***")
        print("*************************************************************")
        sys.exit(1)
    if args.validate_config:
        print("*************************************************************")
        print("*** Your config file is valid.                            ***")
        print("*************************************************************")
        sys.exit(0)

    # Run the main application.
    FrigateApp(config).start()


if __name__ == "__main__":
    main()
