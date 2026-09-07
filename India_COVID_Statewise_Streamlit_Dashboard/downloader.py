import os, requests

URL = "https://raw.githubusercontent.com/imdevskp/covid-19-india-data/refs/heads/master/state_level_daily.csv"
OUT = os.path.join("data", "covid_india_statewise.csv")

def download():
    os.makedirs("data", exist_ok=True)
    r = requests.get(URL, timeout=30)
    r.raise_for_status()
    with open(OUT, "wb") as f:
        f.write(r.content)
    return OUT

if __name__ == "__main__":
    print("Downloading full dataset...")
    print(download())
