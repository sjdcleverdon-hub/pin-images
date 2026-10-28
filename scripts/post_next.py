"""Post the next queued pin to Pinterest through Composio, then mark it posted in queue.json."""
import json, os, sys, datetime

from composio import Composio

REPO = os.environ["GITHUB_REPOSITORY"]
BRANCH = os.environ.get("GITHUB_REF_NAME", "main")
ACCOUNT = os.environ["COMPOSIO_CONNECTED_ACCOUNT_ID"]

with open("queue.json") as f:
    queue = json.load(f)

item = next((q for q in queue if q.get("status") == "queued"), None)
if item is None:
    print("Queue is empty: nothing to post.")
    sys.exit(0)

arguments = {
    "board_id": item["board_id"],
    "title": item["title"],
    "description": item["description"],
    "link": item["link"],
    "alt_text": item.get("alt_text", ""),
    "media_source": {
        "source_type": "image_url",
        "url": f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{item['image']}",
    },
}

client = Composio(api_key=os.environ["COMPOSIO_API_KEY"])
result = client.tools.execute(
    "PINTEREST_CREATE_PIN",
    arguments=arguments,
    connected_account_id=ACCOUNT,
    dangerously_skip_version_check=True,
)
print(json.dumps(result, indent=2, default=str)[:3000])

if not result.get("successful"):
    print("Pinterest post failed. Queue left unchanged.")
    sys.exit(1)

data = result.get("data") or {}
pin_id = data.get("id") or (data.get("response_data") or {}).get("id")
item["status"] = "posted"
item["pin_id"] = pin_id
item["posted_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
with open("queue.json", "w") as f:
    json.dump(queue, f, indent=2)
    f.write("\n")
print(f"Posted pin {pin_id}")
