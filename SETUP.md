# Content Automation — Make.com Replacement

Everything now lives inside the `ignaciotorano-site` repo. No Make, no Cloudinary,
no Google Sheets. GitHub Actions generates drafts, a pull request is your approval
email, and merging publishes to both Google Business Profile and the website.

## How it works

1. **Every day at 9 AM ET** — `generate-post.yml` runs. It picks the next topic
   from `automation/topics.csv`, calls the Claude API, and generates a GBP post
   plus a full blog article in your locked voice (Hook → Reward → Issue →
   Solution, first-person grounding line, South Tampa references).
2. **A pull request opens** — GitHub emails you. The PR body shows the full GBP
   post, the article lead, and a link to the blog file. Edit anything directly
   in the PR if you want.
3. **Your image** — open the PR, write a comment, and drag your image into
   the comment box, then post it. The `attach-image` workflow saves it as the
   post's feature image on the branch and replies with a ✅. This works from
   your phone. Skip it and the blog hides the image; the GBP post goes out
   text-only. (Manual alternative: upload the file yourself to the branch as
   `blog/<slug>/<slug>-feature.png`.)
4. **Merge = publish.** The merge triggers:
   - `publish-gbp.yml` → posts to Google Business Profile (it waits for Netlify
     to deploy first so it can attach your image straight from
     `ignaciotorano.com` — this replaces Cloudinary)
   - your existing `rebuild-blog.yml` → regenerates blog.html + sitemap
   - Netlify → redeploys the site with the new article
5. **Close the PR instead** to discard a draft. Nothing publishes.

When all 100 topics are used up, the script asks Claude to invent a fresh topic
automatically and appends it to the CSV — the system never stops.

## One-time setup

### 1. Put every file in its place

The zip mirrors the repo exactly — same folder names, same paths. Copy each
item to the identical location inside `ignaciotorano-site`:

```
WHAT (from the zip)                      WHERE (in your repo)
---------------------------------------  -------------------------------------
build_site.py                            REPLACES build_site.py at repo root
automation/generate_post.py              automation/  (new folder at root)
automation/publish_gbp.py                automation/
automation/attach_image.py               automation/
automation/blog_template.html            automation/
automation/topics.csv                    automation/
automation/pending/.gitkeep              automation/pending/
automation/posted/.gitkeep               automation/posted/
.github/workflows/generate-post.yml      .github/workflows/  (next to rebuild-blog.yml)
.github/workflows/publish-gbp.yml        .github/workflows/
.github/workflows/attach-image.yml       .github/workflows/
```

Nothing else in the repo changes. Your existing `rebuild-blog.yml` stays.

### 2. Add repo secrets

Repo → Settings → Secrets and variables → Actions → New repository secret:

| Secret | Where it comes from |
|---|---|
| `ANTHROPIC_API_KEY` | console.anthropic.com — the same key Make was using |
| `GBP_CLIENT_ID` | Google Cloud OAuth client — same one from your Make setup |
| `GBP_CLIENT_SECRET` | Same OAuth client |
| `GBP_REFRESH_TOKEN` | See below |
| `GBP_ACCOUNT_ID` | Numeric account ID from the Business Profile API |
| `GBP_LOCATION_ID` | Numeric location ID for your listing |

**Getting the refresh token:** use Google's OAuth Playground
(developers.google.com/oauthplayground). Click the gear icon → "Use your own
OAuth credentials" → paste your client ID/secret. Authorize scope
`https://www.googleapis.com/auth/business.manage`, then exchange the code —
copy the refresh token it returns. (Add
`https://developers.google.com/oauthplayground` as an authorized redirect URI
on your OAuth client first.)

**Getting account/location IDs:** with an access token, call
`https://mybusinessaccountmanagement.googleapis.com/v1/accounts` (account ID is
the number after `accounts/`), then
`https://mybusinessbusinessinformation.googleapis.com/v1/accounts/<ID>/locations?readMask=name,title`
(location ID is the number after `locations/`).

### 3. Allow Actions to open PRs

Repo → Settings → Actions → General → Workflow permissions:
- select **Read and write permissions**
- check **Allow GitHub Actions to create and approve pull requests**

### 4. Make sure PR emails reach you

github.com → Settings → Notifications: Participating & @mentions → Email on.
You'll get an email the moment each draft PR opens.

### 5. Test it

Repo → Actions → "Generate post draft (PR for approval)" → Run workflow.
A PR should appear within ~2 minutes. Merge it and watch the publish run in
the Actions tab.

## Notes

- The topics CSV shows all 100 rows as `N` because the old Make system tracked
  posting in Google Sheets. Round two through the same topics is intentional —
  each run generates a completely fresh take, and now every topic also gets a
  blog article your site never had. If you'd rather skip some, change their
  `Posted` to `Y`.
- Schedule lives in `generate-post.yml` (`cron: '0 13 * * *'` = every day
  9 AM EDT). During Eastern Standard Time change 13 to 14.
- If a GBP publish fails (expired token, API hiccup), the post stays in
  `automation/pending/` and retries on the next merge — or run the publish
  workflow manually from the Actions tab.
