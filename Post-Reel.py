import requests, time, os, json, glob

IG_USER_ID = os.getenv("IG_USER_ID")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
# Folder with mp4 files (in repo)
VIDEO_DIR = "videos"
POSTED_LOG = "posted.json"

def get_next_video():
    posted = []
    if os.path.exists(POSTED_LOG):
        with open(POSTED_LOG) as f:
            posted = json.load(f)
    all_videos = sorted(glob.glob(f"{VIDEO_DIR}/*.mp4"))
    for v in all_videos:
        if v not in posted:
            return v, posted
    return None, posted

def upload_to_public_url():
    # If you use GitHub repo videos, you need a public URL.
    # Option A: Use a free file host or convert to public raw GitHub URL
    # For simplicity, this example expects VIDEO_URL to be public.
    # If videos are in repo, we upload via transfer.sh (free temporary)
    # Replace with your permanent CDN if you have one.
    video_path, posted = get_next_video()
    if not video_path:
        print("No new videos")
        return None, None, posted
    # For GitHub Actions, raw URL: https://raw.githubusercontent.com/USER/REPO/main/videos/file.mp4
    # User must set this as env or we build it
    # Here we just return local path and expect you to host on Drive with public link
    return video_path, video_path, posted

def post_reel(video_url, caption):
    # For Graph API, video_url must be publicly accessible https
    # If you host on Drive: https://drive.google.com/uc?export=download&id=FILE_ID
    url = f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media"
    payload = {
        "media_type": "REELS",
        "video_url": video_url,
        "caption": caption,
        "access_token": ACCESS_TOKEN
    }
    r = requests.post(url, data=payload)
    print("Create container:", r.text)
    data = r.json()
    if "id" not in data:
        raise Exception(f"Container failed: {data}")
    creation_id = data["id"]
    time.sleep(70)  # wait for processing
    pub_url = f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media_publish"
    pub = requests.post(pub_url, data={"creation_id": creation_id, "access_token": ACCESS_TOKEN})
    print("Publish:", pub.text)
    return pub.json()

if __name__ == "__main__":
    # Example: if you use public GitHub raw URLs
    video_file, _, posted = get_next_video()
    if not video_file:
        print("All videos posted")
        exit(0)
    # Build public URL - CHANGE USER/REPO
    # Replace with your actual GitHub username/repo
    PUBLIC_BASE = os.getenv("PUBLIC_VIDEO_BASE")  # e.g. https://raw.githubusercontent.com/deep/bot/main/videos
    video_name = os.path.basename(video_file)
    public_url = f"{PUBLIC_BASE}/{video_name}" if os.getenv("PUBLIC_VIDEO_BASE") else None
    
    # If you use Drive links, set VIDEO_URL env directly for testing
    video_url = os.getenv("VIDEO_URL") or public_url
    if not video_url:
        print(f"Set PUBLIC_VIDEO_BASE or VIDEO_URL. Local file ready: {video_file}")
        exit(1)
    
    caption = os.getenv("CAPTION") or f"Lost in Lucknow, found in every city 🌿 | {video_name} #lucknow #reels"
    result = post_reel(video_url, caption)
    # log
    posted.append(video_file)
    with open(POSTED_LOG, "w") as f:
        json.dump(posted, f)
