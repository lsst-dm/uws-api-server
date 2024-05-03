import os
import time

import requests

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(description="Monitor incoming data to launch pipeline job")
    parser.add_argument("--id", dest="id", type=str, nargs="?", help="Job ID", required=True)
    parser.add_argument("--type", dest="duration", type=str, nargs="?", help="Job type", required=True)
    parser.add_argument(
        "--api_url", dest="api_url", type=str, nargs="?", help="API endpoint URL", required=True
    )
    args = parser.parse_args()

    polling_interval = 5
    launch_job = False
    filename = f"{args.id}.dat"
    while not launch_job:
        # For testing purposes, if the file named "[job_id].dat" appears
        # then the job is triggered
        if os.path.isfile(filename):
            print(f'Data file "{filename}" found. Making API request...')
            launch_job = True
            # Inform the JobManager that the data is available
            r = requests.get(
                args.api_url,
                params={
                    "id": args.id,
                },
            )
        else:
            # print('Data "{}" has not arrived. Sleeping...'.format(filename))
            time.sleep(polling_interval)
