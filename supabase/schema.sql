create table if not exists public.usage_surveys (
    id uuid primary key default gen_random_uuid(),
    hangullo_version text not null,
    os text not null,
    usage_type text not null,
    experience_level text not null,
    discovery_source text not null,
    usage_frequency text not null,
    created_at timestamptz not null default now()
);

create table if not exists public.experience_surveys (
    id uuid primary key default gen_random_uuid(),
    hangullo_version text not null,
    os text not null,
    grammar_ease smallint not null check (grammar_ease between 1 and 5),
    ide_ease smallint not null check (ide_ease between 1 and 5),
    recommendation_score smallint not null check (recommendation_score between 1 and 5),
    best_point text not null default '',
    worst_point text not null default '',
    desired_features jsonb not null default '[]'::jsonb,
    satisfaction smallint not null check (satisfaction between 1 and 5),
    feedback text not null default '',
    created_at timestamptz not null default now()
);

create table if not exists public.bug_reports (
    id uuid primary key default gen_random_uuid(),
    hangullo_version text not null,
    os text not null,
    python_version text not null,
    error_type text not null,
    title text not null,
    description text not null,
    reproduction_steps text not null default '',
    expected_result text not null default '',
    actual_result text not null default '',
    error_log text not null default '',
    created_at timestamptz not null default now(),
    status text not null default 'new'
);

create table if not exists public.feature_requests (
    id uuid primary key default gen_random_uuid(),
    hangullo_version text not null,
    os text not null,
    title text not null,
    description text not null,
    reason text not null default '',
    example text not null default '',
    created_at timestamptz not null default now(),
    status text not null default 'new'
);

create table if not exists public.app_updates (
    id uuid primary key default gen_random_uuid(),
    version text not null unique,
    download_url text not null,
    release_notes text not null default '',
    mandatory boolean not null default false,
    published_at timestamptz not null default now()
);

alter table public.usage_surveys enable row level security;
alter table public.experience_surveys enable row level security;
alter table public.bug_reports enable row level security;
alter table public.feature_requests enable row level security;
alter table public.app_updates enable row level security;

grant usage on schema public to anon;

revoke all on table
    public.usage_surveys,
    public.experience_surveys,
    public.bug_reports,
    public.feature_requests,
    public.app_updates
 from public, anon, authenticated;

grant insert on table
    public.usage_surveys,
    public.experience_surveys,
    public.bug_reports,
    public.feature_requests
to anon;

grant select (version, download_url, release_notes, mandatory, published_at)
on table public.app_updates to anon;

drop policy if exists usage_surveys_anon_insert on public.usage_surveys;
create policy usage_surveys_anon_insert on public.usage_surveys
    for insert to anon with check (true);

drop policy if exists experience_surveys_anon_insert on public.experience_surveys;
create policy experience_surveys_anon_insert on public.experience_surveys
    for insert to anon with check (true);

drop policy if exists bug_reports_anon_insert on public.bug_reports;
create policy bug_reports_anon_insert on public.bug_reports
    for insert to anon with check (true);

drop policy if exists feature_requests_anon_insert on public.feature_requests;
create policy feature_requests_anon_insert on public.feature_requests
    for insert to anon with check (true);

drop policy if exists app_updates_anon_read_published on public.app_updates;
create policy app_updates_anon_read_published on public.app_updates
    for select to anon using (published_at <= now());