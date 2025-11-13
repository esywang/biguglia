-- Create organizations table
CREATE TABLE IF NOT EXISTS public.organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT (now() AT TIME ZONE 'utc'),
    updated_at TIMESTAMPTZ DEFAULT (now() AT TIME ZONE 'utc')
);

-- Create organization_members table (links users to organizations)
CREATE TABLE IF NOT EXISTS public.organization_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('owner', 'admin', 'member')),
    created_at TIMESTAMPTZ DEFAULT (now() AT TIME ZONE 'utc'),
    UNIQUE(organization_id, user_id)
);

-- Create github_connections table (stores GitHub App installations)
CREATE TABLE IF NOT EXISTS public.github_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    github_installation_id BIGINT UNIQUE NOT NULL,
    github_account_login TEXT NOT NULL,
    access_token TEXT, -- Will be encrypted
    created_at TIMESTAMPTZ DEFAULT (now() AT TIME ZONE 'utc'),
    updated_at TIMESTAMPTZ DEFAULT (now() AT TIME ZONE 'utc')
);

-- Add organization_id to existing tables
ALTER TABLE public.github_pr_merge
    ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES public.organizations(id) ON DELETE CASCADE;

ALTER TABLE public.dbt_model_changes
    ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES public.organizations(id) ON DELETE CASCADE;

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_organization_members_user_id ON public.organization_members(user_id);
CREATE INDEX IF NOT EXISTS idx_organization_members_org_id ON public.organization_members(organization_id);
CREATE INDEX IF NOT EXISTS idx_github_connections_org_id ON public.github_connections(organization_id);
CREATE INDEX IF NOT EXISTS idx_github_pr_merge_org_id ON public.github_pr_merge(organization_id);
CREATE INDEX IF NOT EXISTS idx_dbt_model_changes_org_id ON public.dbt_model_changes(organization_id);

-- Enable Row Level Security (RLS) on all tables
ALTER TABLE public.organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.organization_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.github_connections ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.github_pr_merge ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.dbt_model_changes ENABLE ROW LEVEL SECURITY;

-- RLS Policies for organizations table
-- Users can only see organizations they are members of
CREATE POLICY "Users can view their organizations"
    ON public.organizations
    FOR SELECT
    USING (
        id IN (
            SELECT organization_id
            FROM public.organization_members
            WHERE user_id = auth.uid()
        )
    );

-- Only owners can update organizations
CREATE POLICY "Owners can update their organizations"
    ON public.organizations
    FOR UPDATE
    USING (
        id IN (
            SELECT organization_id
            FROM public.organization_members
            WHERE user_id = auth.uid() AND role = 'owner'
        )
    );

-- RLS Policies for organization_members table
CREATE POLICY "Users can view members of their organizations"
    ON public.organization_members
    FOR SELECT
    USING (
        organization_id IN (
            SELECT organization_id
            FROM public.organization_members
            WHERE user_id = auth.uid()
        )
    );

-- Only owners and admins can manage members
CREATE POLICY "Owners and admins can manage members"
    ON public.organization_members
    FOR ALL
    USING (
        organization_id IN (
            SELECT organization_id
            FROM public.organization_members
            WHERE user_id = auth.uid() AND role IN ('owner', 'admin')
        )
    );

-- RLS Policies for github_connections table
CREATE POLICY "Users can view their org's GitHub connections"
    ON public.github_connections
    FOR SELECT
    USING (
        organization_id IN (
            SELECT organization_id
            FROM public.organization_members
            WHERE user_id = auth.uid()
        )
    );

-- Only owners and admins can manage GitHub connections
CREATE POLICY "Owners and admins can manage GitHub connections"
    ON public.github_connections
    FOR ALL
    USING (
        organization_id IN (
            SELECT organization_id
            FROM public.organization_members
            WHERE user_id = auth.uid() AND role IN ('owner', 'admin')
        )
    );

-- RLS Policies for github_pr_merge table
CREATE POLICY "Users can view their org's PR data"
    ON public.github_pr_merge
    FOR SELECT
    USING (
        organization_id IN (
            SELECT organization_id
            FROM public.organization_members
            WHERE user_id = auth.uid()
        )
    );

-- Service role can insert/update (for webhook processing)
CREATE POLICY "Service role can manage PR data"
    ON public.github_pr_merge
    FOR ALL
    USING (auth.jwt()->>'role' = 'service_role');

-- RLS Policies for dbt_model_changes table
CREATE POLICY "Users can view their org's model changes"
    ON public.dbt_model_changes
    FOR SELECT
    USING (
        organization_id IN (
            SELECT organization_id
            FROM public.organization_members
            WHERE user_id = auth.uid()
        )
    );

-- Service role can insert/update (for webhook processing)
CREATE POLICY "Service role can manage model changes"
    ON public.dbt_model_changes
    FOR ALL
    USING (auth.jwt()->>'role' = 'service_role');

-- Grant permissions to authenticated users
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT ALL ON public.organizations TO authenticated;
GRANT ALL ON public.organization_members TO authenticated;
GRANT ALL ON public.github_connections TO authenticated;
GRANT SELECT ON public.github_pr_merge TO authenticated;
GRANT SELECT ON public.dbt_model_changes TO authenticated;

-- Service role needs full access
GRANT ALL ON public.organizations TO service_role;
GRANT ALL ON public.organization_members TO service_role;
GRANT ALL ON public.github_connections TO service_role;
GRANT ALL ON public.github_pr_merge TO service_role;
GRANT ALL ON public.dbt_model_changes TO service_role;
