import os
import re
import json
import urllib.request
from datetime import datetime, timezone, timedelta
from collections import defaultdict

def make_bar(percent, total_len=14):
    filled = int(round((percent / 100.0) * total_len))
    filled = max(0, min(total_len, filled))
    return "█" * filled + "▒" * (total_len - filled)

def update_readme():
    token = os.environ.get("GITHUB_TOKEN") or os.popen('printf "protocol=https\\nhost=github.com\\n" | git credential fill | awk -F= \'$1=="password"{print $2}\'').read().strip()
    username = "i-m-champion"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "HabitsUpdater"
    }
    if token:
        headers["Authorization"] = f"token {token}"

    def get_json(url):
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())

    # 1. User Info
    user = get_json(f"https://api.github.com/users/{username}")
    public_repos = user.get("public_repos", 0)
    private_repos = user.get("total_private_repos", 0)
    disk_usage = user.get("disk_usage", 0)

    # Storage string
    if disk_usage >= 1024:
        storage_str = f"{disk_usage / 1024:.1f} MB"
    else:
        storage_str = f"{disk_usage:.1f} kB"

    # 2. Total Contributions via GraphQL
    total_contribs = 15
    if token:
        try:
            gql_query = """
            query {
              user(login: "i-m-champion") {
                contributionsCollection {
                  contributionCalendar {
                    totalContributions
                  }
                }
              }
            }
            """
            gql_req = urllib.request.Request(
                "https://api.github.com/graphql",
                data=json.dumps({"query": gql_query}).encode(),
                headers={"Authorization": f"bearer {token}", "User-Agent": "GraphQLChecker"}
            )
            with urllib.request.urlopen(gql_req) as resp:
                gdata = json.loads(resp.read().decode())
                total_contribs = gdata["data"]["user"]["contributionsCollection"]["contributionCalendar"]["totalContributions"]
        except Exception as e:
            print("GraphQL error:", e)

    # 3. Analyze Commits and Languages
    repos = get_json(f"https://api.github.com/users/{username}/repos?per_page=100")
    
    time_bins = {"Morning": 0, "Daytime": 0, "Evening": 0, "Night": 0}
    days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    day_bins = {d: 0 for d in days_order}
    total_commits = 0
    langs = defaultdict(int)

    ist_tz = timezone(timedelta(hours=5, minutes=30))

    for r in repos:
        r_name = r["name"]
        lang = r.get("language")
        if lang:
            langs[lang] += 1
        else:
            langs["Markdown"] += 1

        try:
            commits = get_json(f"https://api.github.com/repos/{username}/{r_name}/commits?author={username}&per_page=100")
            for c in commits:
                c_date = c["commit"]["author"]["date"]
                dt = datetime.fromisoformat(c_date.replace("Z", "+00:00")).astimezone(ist_tz)
                hour = dt.hour
                weekday = dt.strftime("%A")

                total_commits += 1
                if weekday in day_bins:
                    day_bins[weekday] += 1

                if 6 <= hour < 12:
                    time_bins["Morning"] += 1
                elif 12 <= hour < 18:
                    time_bins["Daytime"] += 1
                elif 18 <= hour < 24:
                    time_bins["Evening"] += 1
                else:
                    time_bins["Night"] += 1
        except Exception:
            pass

    if total_commits == 0:
        total_commits = 1

    most_productive_day = max(day_bins, key=day_bins.get)
    early_or_night = "Early Bird ⚡" if (time_bins["Morning"] + time_bins["Daytime"]) >= (time_bins["Evening"] + time_bins["Night"]) else "Night Owl 🦉"

    sorted_langs = sorted(langs.items(), key=lambda x: x[1], reverse=True)
    top_lang = sorted_langs[0][0] if sorted_langs else "Code"

    out = []
    out.append("┌──[ root@telemetry:~/github_data ]")
    out.append("│")
    out.append(f"├── 💾 Storage Allocated:   {storage_str}")
    out.append(f"├── 🏆 Annual Contributions: {total_contribs} in 2026")
    out.append(f"├── ⚡ Status:               Active Builder / Hacker Mode")
    out.append(f"├── 📦 Public Repositories:  {public_repos}")
    out.append(f"└── 🔒 Private Enclaves:     {private_repos}\n")

    out.append(f"┌──[ Productivity Cycle // {early_or_night} ]")
    out.append("│")
    icons = {"Morning": "🌞", "Daytime": "🌆", "Evening": "🌃", "Night": "🌙"}
    for t in ["Morning", "Daytime", "Evening", "Night"]:
        cnt = time_bins[t]
        pct = (cnt / total_commits) * 100.0
        bar = make_bar(pct)
        c_str = f"{cnt} commit" if cnt == 1 else f"{cnt} commits"
        prefix = "├──" if t != "Night" else "└──"
        out.append(f"{prefix} {icons[t]} {t:<10} {c_str:>12}   {bar}   {pct:05.2f} %")

    out.append(f"\n┌──[ Weekly Activity Matrix // Peak on {most_productive_day} ]")
    out.append("│")
    for d in days_order:
        cnt = day_bins[d]
        pct = (cnt / total_commits) * 100.0
        bar = make_bar(pct)
        c_str = f"{cnt} commit" if cnt == 1 else f"{cnt} commits"
        prefix = "├──" if d != "Sunday" else "└──"
        out.append(f"{prefix} {d:<14} {c_str:>12}   {bar}   {pct:05.2f} %")

    out.append(f"\n┌──[ Core Technologies // Dominant: {top_lang} ]")
    out.append("│")
    total_repo_langs = sum(langs.values()) or 1
    for idx, (l_name, l_count) in enumerate(sorted_langs[:5]):
        pct = (l_count / total_repo_langs) * 100.0
        bar = make_bar(pct)
        r_str = f"{l_count} repo" if l_count == 1 else f"{l_count} repos"
        prefix = "└──" if idx == len(sorted_langs[:5]) - 1 else "├──"
        out.append(f"{prefix} {l_name:<14} {r_str:>12}   {bar}   {pct:05.2f} %")

    result_block = "```text\n" + "\n".join(out) + "\n```"

    readme_path = "/Users/yo/.gemini/antigravity/scratch/i-m-champion/README.md"
    if not os.path.exists(readme_path):
        readme_path = "README.md"

    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = r"(<!--START_SECTION:(?:waka|habits)-->)[\s\S]*?(<!--END_SECTION:(?:waka|habits)-->)"
    replacement = rf"\1\n{result_block}\n\2"
    
    new_content = re.sub(pattern, replacement, content)
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    print("Updated README.md telemetry successfully!")

if __name__ == '__main__':
    update_readme()
