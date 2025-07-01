import argparse
import os
import time
from urllib.parse import urlparse

import httpx
from contextual import ContextualAI
from dotenv import load_dotenv

load_dotenv()

CTXL_API_KEY = os.getenv("CTXL_API_KEY")


def submit_parse_job(file_path: str, polling_interval_s: int = 30):
    """Submits a file to the /parse endpoint and waits for completion."""
    if not CTXL_API_KEY:
        raise ValueError("CTXL_API_KEY environment variable not set.")

    client = ContextualAI(api_key=CTXL_API_KEY)

    print(f"Submitting '{file_path}' for parsing...")
    with open(file_path, "rb") as fp:
        response = client.parse.create(
            raw_file=fp,
            parse_mode="standard",
            enable_document_hierarchy=True,
        )

    job_id = response.job_id
    print(f"Parse job submitted. Job ID: {job_id}")
    print(
        f"You can view the job in the UI at: https://app.contextual.ai/{{tenant}}/components/parse?job={job_id}"
    )
    print("(Remember to replace {tenant} with your workspace name)")

    print("Waiting for job to complete...")
    while True:
        try:
            result = client.parse.job_status(job_id)
            status = result.status
            print(f"Job status: {status}")
            if status == "completed":
                print(f"Job completed successfully. Job ID: {job_id}")
                break
            elif status in ["failed", "cancelled"]:
                print(f"Job {status}. Aborting.")
                break
            time.sleep(polling_interval_s)
        except Exception as e:
            print(f"An error occurred while checking job status: {e}")
            break

    return job_id


def download_file(url: str, output_dir: str = "."):
    """Downloads a file from a URL."""
    try:
        response = httpx.get(url, follow_redirects=True)
        response.raise_for_status()

        # get filename from URL
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        if not filename:
            filename = "downloaded_file"  # fallback

        file_path = os.path.join(output_dir, filename)

        with open(file_path, "wb") as f:
            f.write(response.content)

        print(f"File downloaded to {file_path}")
        return file_path
    except httpx.RequestError as e:
        print(f"Error downloading file: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Submit a document to the Contextual AI /parse API."
    )
    parser.add_argument("path_or_url", help="Local file path or URL to the document.")
    args = parser.parse_args()

    path_or_url = args.path_or_url

    downloaded_file_path = None
    try:
        if urlparse(path_or_url).scheme in ("http", "https"):
            print(f"Input is a URL: {path_or_url}")
            file_path = download_file(path_or_url)
            if not file_path:
                return
            downloaded_file_path = file_path
        elif os.path.isfile(path_or_url):
            print(f"Input is a local file: {path_or_url}")
            file_path = path_or_url
        else:
            print(f"Error: Input '{path_or_url}' is not a valid file path or URL.")
            return

        submit_parse_job(file_path)

    finally:
        if downloaded_file_path:
            # Clean up the downloaded file
            print(f"Cleaning up downloaded file: {downloaded_file_path}")
            os.remove(downloaded_file_path)


if __name__ == "__main__":
    main()
