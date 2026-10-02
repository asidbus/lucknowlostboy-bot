import requests, time, os, json, glob, sys

print("=== BOT START ===")
print(f"Repo: {os.getenv('GITHUB_REPOSITORY')}")

IG_USER_ID = os.getenv("IG_USER_ID")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
VIDEO_DIR = "videos"

if not IG_USER_ID:
    print("ERROR: IG_USER_ID secret missing! Add in Settings > Secrets > Actions")
    sys.exit(2)
if not ACCESS_TOKEN:
    print("ERROR: ACCESS_TOKEN secret missing!")
    sys.exit(2)

print(f"IG_USER_ID found: {IG_USER_ID[:5]}... (length {len(IG_USER_ID)})")
print(f"Token found: {ACCESS_TOKEN[:10]}... (length {len(ACCESS_TOKEN)})")

# list files
print(f"Listing {VIDEO_DIR}:")
if not os.path.exists(VIDEO_DIR):
    print(f"ERROR: folder {VIDEO_DIR} not found at root!")
    print("Root files:", os.listdir("."))
    sys.exit(2)

videos = sorted(glob.glob(f"{VIDEO_DIR}/*.mp4"))
print(f"Found {len(videos)} videos: {videos}")
if not videos:
    print("ERROR: No mp4 in videos/ folder. Upload at least 1 mp4.")
    sys.exit(2)

# posted log
POSTED_LOG = "posted.json"
posted = []
if os.path.exists(POSTED_LOG):
    try:
        with open(POSTED_LOG) as f:
            posted = json.load(f)
    except:
        posted = []

next_video = None
for v in videos:
    if v not in posted:
        next_video = v
        break

if not next_video:
    print("All videos already posted. Upload new ones.")
    sys.exit(0)

print(f"Next to post: {next_video}")

# Build public URL - GitHub raw
repo = os.getenv("GITHUB_REPOSITORY")  # e.g. user/repo
if not repo:
    print("ERROR: GITHUB_REPOSITORY env missing")
    sys.exit(2)

public_url = f"https://raw.githubusercontent.com/{repo}/main/{next_video}"
print(f"Public URL: {public_url}")

caption = os.getenv("CAPTION") or f"Lost in Lucknow 🌿 {os.path.basename(next_video)} #lucknow"

# 1. Create container
print("Creating container...")
url = f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media"
payload = {
    "media_type": "REELS",
    "video_url": public_url,
    "caption": caption,
    "access_token": ACCESS_TOKEN
}
r = requests.post(url, data=payload)
print(f"Container response {r.status_code}: {r.text}")
data = r.json()
if "id" not in data:
    print(f"FAILED to create container: {data}")
    sys.exit(2)

creation_id = data["id"]
print(f"Container ID: {creation_id}, waiting 75s for processing...")
time.sleep(75)

# 2. Publish
pub_url = f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media_publish"
pub = requests.post(pub_url, data={"creation_id": creation_id, "access_token": ACCESS_TOKEN})
print(f"Publish response {pub.status_code}: {pub.text}")
result = pub.json()
if "id" in result:
    print(f"SUCCESS! Reel published: {result['id']}")
    posted.append(next_video)
    with open(POSTED_LOG, "w") as f:
        json.dump(posted, f)
else:
    print(f"Publish failed: {result}")
    sys.exit(2)
