# db-deploy-legacy — Databricks CI/CD without DABs

Legacy-style deployment of **notebooks** and **jobs** to a Databricks workspace using two separate GitHub Actions — no Declarative Automation Bundles (DABs), no `databricks bundle` commands. Everything is done with the Databricks CLI against the Jobs API 2.1 and the Repos API.

## Repository structure

```
db-deploy-legacy/
├── notebooks/                      # Folder 1: notebooks (the "code")
│   └── hello_job_notebook.py       # Sample notebook (Databricks source format)
├── workflows/                      # Folder 2: workflows (job definitions)
│   └── legacy_hello_job.json       # Sample job definition (Jobs API 2.1 settings)
└── .github/workflows/
    ├── deploy-code.yml             # Action 1: sync code into the Databricks Git folder
    └── deploy-job.yml              # Action 2: create or update the Databricks job
```

## How it works

```
           push to main
                │
   ┌────────────┴─────────────┐
   │ changed notebooks/**     │ changed workflows/**
   ▼                          ▼
 deploy-code.yml           deploy-job.yml
   │                          │
   │ databricks repos update  │ 1. jobs list -> find job by name
   │ (pull latest into the     │ 2. exists  -> jobs reset  (update, same ID)
   │  Databricks Git folder)   │ 3. missing -> jobs create
   ▼                          ▼
 Databricks Git folder      Databricks job "legacy-hello-job"
 /Repos/.../db-deploy-legacy   └─ notebook task points INTO the Git folder
```

* **Action 1 — deploy-code.yml**: triggers on pushes that change `notebooks/**`. It runs `databricks repos update`, which pulls the latest commit from GitHub into the workspace **Git folder** (`/Repos/sivaashok111@outlook.com/db-deploy-legacy`). The notebooks never get copied anywhere else — the job runs them straight out of the Git folder.
* **Action 2 — deploy-job.yml**: triggers on pushes that change `workflows/**`. It lists the workspace jobs, finds the one whose `name` matches the JSON definition (`legacy-hello-job`), and either **resets** (updates) the existing job in place or **creates** it if it does not exist.

## One-time setup

### 1. Create the Databricks Git folder

In the Databricks workspace, add a Git folder (Repos) that clones this GitHub repo, e.g. at `/Repos/sivaashok111@outlook.com/db-deploy-legacy`, with branch `main` checked out. If you place it somewhere else, update `GIT_FOLDER_PATH` in both workflow files.

### 2. Create a Databricks access token (PAT)

User Settings → Developer → Access tokens. The token's user needs permission to update the Git folder and to create/reset jobs.

### 3. Add GitHub repository secrets

In GitHub: repo → Settings → Secrets and variables → Actions → New repository secret:

| Secret | Value |
| --- | --- |
| `DATABRICKS_HOST` | `https://dbc-692905b3-023b.cloud.databricks.com` |
| `DATABRICKS_TOKEN` | the PAT from step 2 |

## The sample job

`workflows/legacy_hello_job.json` defines `legacy-hello-job` — a single notebook task with no cluster spec, so it runs on serverless jobs compute. The notebook path is a `__GIT_FOLDER_PATH__` placeholder that the workflow replaces with the real Git folder path (single source of truth, defined once as `GIT_FOLDER_PATH` in the workflow env).

To add more jobs: drop another JSON file in `workflows/` following the same pattern and extend `deploy-job.yml` (or parameterize it) to loop over the files.

## Testing the pipeline

1. Push any change under `notebooks/` → watch **Deploy code to Databricks Git folder** run, then check the Git folder in the workspace shows the new commit.
2. Push any change under `workflows/` (or run **Deploy job to Databricks** manually via `workflow_dispatch`) → the first run **creates** `legacy-hello-job` (Jobs UI → Workflows). Run it again → the same job is **updated** in place (same job ID, no duplicate).
3. Run the job manually in the Jobs UI to verify the notebook task executes from the Git folder.

## Important notes

* `jobs reset` **replaces the entire settings** of the job — anything not in the JSON file (schedules, alerts added by hand in the UI) is removed on the next deploy. Keep the JSON as the single source of truth.
* Jobs are matched **by name**; renaming a job in the JSON creates a new job and orphans the old one.
* The notebook path intentionally has **no `.py` extension** — that is how the Jobs API addresses a notebook inside a Git folder.
* `databricks repos update` pulls from GitHub, so the GitHub push must complete first (GitHub Actions guarantees this — the action runs after the push).

* 
