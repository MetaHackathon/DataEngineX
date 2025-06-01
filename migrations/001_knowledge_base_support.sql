-- ============================================================================
-- MIGRATION: Knowledge Base and Enhanced Frontend Support
-- Version: 001
-- Description: Adds knowledge bases, document viewer enhancements, and 
--              all tables needed to support the DelphiX frontend
-- ============================================================================

-- ============================================================================
-- KNOWLEDGE BASE MANAGEMENT TABLES
-- ============================================================================

-- Knowledge bases for grouping papers
CREATE TABLE IF NOT EXISTS knowledge_bases (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  description TEXT,
  tags JSONB DEFAULT '[]',
  is_public BOOLEAN DEFAULT FALSE,
  status TEXT DEFAULT 'active', -- active, archived, deleted
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Junction table for papers in knowledge bases
CREATE TABLE IF NOT EXISTS knowledge_base_papers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  knowledge_base_id UUID NOT NULL REFERENCES knowledge_bases(id) ON DELETE CASCADE,
  paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
  added_at TIMESTAMP DEFAULT NOW(),
  added_by UUID REFERENCES profiles(id),
  UNIQUE(knowledge_base_id, paper_id)
);

-- Knowledge base sharing/collaboration
CREATE TABLE IF NOT EXISTS knowledge_base_shares (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  knowledge_base_id UUID NOT NULL REFERENCES knowledge_bases(id) ON DELETE CASCADE,
  shared_with_user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
  shared_by_user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  permissions TEXT DEFAULT 'read', -- read, write, admin
  public_link_id TEXT UNIQUE, -- For public sharing
  created_at TIMESTAMP DEFAULT NOW(),
  expires_at TIMESTAMP
);

-- AI-generated insights for knowledge bases
CREATE TABLE IF NOT EXISTS knowledge_base_insights (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  knowledge_base_id UUID NOT NULL REFERENCES knowledge_bases(id) ON DELETE CASCADE,
  insights JSONB NOT NULL DEFAULT '[]',
  trends JSONB DEFAULT '[]',
  research_gaps JSONB DEFAULT '[]',
  key_connections JSONB DEFAULT '[]',
  generated_by TEXT DEFAULT 'llama-4', -- AI model used
  generated_at TIMESTAMP DEFAULT NOW(),
  expires_at TIMESTAMP DEFAULT NOW() + INTERVAL '30 days'
);

-- ============================================================================
-- ENHANCED DOCUMENT & ANNOTATION SUPPORT
-- ============================================================================

-- Enhanced highlights table with frontend requirements
-- (Adding missing columns to existing highlights table)
ALTER TABLE highlights ADD COLUMN IF NOT EXISTS comment TEXT;
ALTER TABLE highlights ADD COLUMN IF NOT EXISTS highlight_type TEXT DEFAULT 'text';
ALTER TABLE highlights ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}';

-- Document chat messages (separate from paper chat)
CREATE TABLE IF NOT EXISTS document_chat_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
  role TEXT NOT NULL, -- user, assistant
  content TEXT NOT NULL,
  context JSONB DEFAULT '{}', -- highlights, page context, etc.
  sources JSONB DEFAULT '[]', -- Referenced highlights/annotations
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT NOW()
);

-- Document view analytics
CREATE TABLE IF NOT EXISTS document_views (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
  session_id TEXT,
  pages_viewed JSONB DEFAULT '[]',
  time_spent INTEGER DEFAULT 0, -- seconds
  last_page INTEGER,
  zoom_level FLOAT DEFAULT 1.0,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- ENHANCED SEARCH & DISCOVERY TABLES
-- ============================================================================

-- User search history for improved recommendations
CREATE TABLE IF NOT EXISTS search_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  query TEXT NOT NULL,
  search_type TEXT DEFAULT 'papers', -- papers, library, annotations
  filters JSONB DEFAULT '{}',
  results_count INTEGER DEFAULT 0,
  clicked_results JSONB DEFAULT '[]',
  created_at TIMESTAMP DEFAULT NOW()
);

-- Paper quality scores and metrics
CREATE TABLE IF NOT EXISTS paper_metrics (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
  quality_score INTEGER, -- 0-100
  relevance_score INTEGER, -- 0-100 based on user activity
  venue TEXT,
  h_index INTEGER,
  downloads INTEGER DEFAULT 0,
  saves INTEGER DEFAULT 0,
  calculated_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(paper_id)
);

-- User activity tracking for personalization
CREATE TABLE IF NOT EXISTS user_activity (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  activity_type TEXT NOT NULL, -- paper_view, paper_save, annotation_create, etc.
  entity_type TEXT, -- paper, annotation, highlight, knowledge_base
  entity_id UUID,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT NOW()
); 