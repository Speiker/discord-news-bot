#!/usr/bin/env python

import feedparser
import time
import requests
import json
import sys
import syslog
import creds

discords = creds.news_bot  # from local creds module
feedurl = "https://classic.wowhead.com/news/rss/classic"


def main():
    new_articles = parse()
    if len(new_articles["Articles"]) > 0:
        for article in new_articles["Articles"]:
            post_to_discord(article)


def parse():
    thefeed = feedparser.parse(feedurl)

    feed = thefeed.feed.get("title", "")
    articles = []

    timenow = time.gmtime()
    for entry in thefeed.entries:
        published_time = entry.get("published_parsed", entry.published_parsed)
        # Converts elapsed time since article was published to an hourly format
        timecheck = (
            (time.mktime(timenow) - time.mktime(published_time)) / 60 / 60
        )
        # Check if article has been published in the last hour
        if timecheck < 1:
            # Remove html formatting from description for readability
            description = entry.get("description", "").split("<")[0]
            articles.append(
                {
                    "Title": entry.get("title", ""),
                    "Link": entry.get("link", ""),
                    "Description": description,
                }
            )

    new_articles = {"Site": feed, "Articles": articles}

    return new_articles


def post_to_discord(article):
    data = {}

    data["username"] = "Wowhead Classic News"

    data["embeds"] = []
    embed = {}
    embed["title"] = article["Title"]
    embed["url"] = article["Link"]
    embed["description"] = article["Description"]
    data["embeds"].append(embed)

    for server in discords:
        result = requests.post(
            server["Webhook"],
            data=json.dumps(data),
            headers={"Content-Type": "application/json"},
        )

        try:
            result.raise_for_status()
        except requests.exceptions.HTTPError as err:
            syslog.syslog(syslog.LOG_ERR, err)
        else:
            syslog.syslog(
                syslog.LOG_INFO,
                "Posted successfully to {}, code {}.".format(
                    server["Name"], result.status_code
                ),
            )


if __name__ == "__main__":
    main()
