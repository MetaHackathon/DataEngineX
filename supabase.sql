-- DataEngineX Complete Database Schema
-- NotebookLM Competitor: Research Knowledge Base + PDF Reader
-- Execute this in your Supabase SQL Editor (will clean existing tables)

-- ============================================================================
-- CLEANUP: Remove existing tables (start fresh)
-- ============================================================================
DROP TABLE IF EXISTS annotations CASCADE;
DROP TABLE IF EXISTS paper_chunks CASCADE;

-- ============================================================================
-- CORE USER MANAGEMENT
-- ============================================================================

-- Create profiles table (extends Supabase auth.users with additional fields)
CREATE TABLE IF NOT EXISTS profiles (
  id UUID REFERENCES auth.users ON DELETE CASCADE,
  full_name TEXT,
  avatar_url TEXT,
  subscription_tier TEXT DEFAULT 'free', -- free, pro, enterprise
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  PRIMARY KEY (id)
);

-- ============================================================================
-- PAPER MANAGEMENT & STORAGE
-- ============================================================================

-- Complete paper records with full metadata
CREATE TABLE papers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  paper_id TEXT NOT NULL, -- ArXiv ID, DOI, or custom ID
  title TEXT NOT NULL,
  abstract TEXT,
  authors JSONB NOT NULL DEFAULT '[]',
  year INTEGER,
  topics JSONB DEFAULT '[]',
  pdf_url TEXT NOT NULL,
  pdf_file_path TEXT, -- For uploaded files
  full_text TEXT, -- Complete extracted text
  citations INTEGER DEFAULT 0,
  institution TEXT,
  impact_score FLOAT DEFAULT 0.0,
  processing_status TEXT DEFAULT 'pending', -- pending, processing, completed, failed, error
  metadata JSONB DEFAULT '{}', -- Additional paper metadata
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(user_id, paper_id)
);

-- Processed text chunks for RAG and search
CREATE TABLE paper_chunks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
  chunk_id TEXT NOT NULL,
  content TEXT NOT NULL,
  page_number INTEGER,
  section TEXT,
  chunk_index INTEGER,
  bbox JSONB, -- Bounding box coordinates {x, y, width, height}
  embedding VECTOR(1536), -- For semantic search (OpenAI embeddings)
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(user_id, chunk_id)
);

-- ============================================================================
-- PDF READER & ANNOTATIONS
-- ============================================================================

-- In-document highlights (text selections)
CREATE TABLE highlights (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
  highlight_text TEXT NOT NULL,
  page_number INTEGER NOT NULL,
  position JSONB NOT NULL, -- {start, end, rects: [{x, y, width, height}]}
  color TEXT DEFAULT 'yellow', -- highlight color
  created_at TIMESTAMP DEFAULT NOW()
);

-- Annotations (notes tied to highlights or general paper)
CREATE TABLE annotations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
  highlight_id UUID REFERENCES highlights(id) ON DELETE CASCADE, -- Optional: tied to highlight
  content TEXT NOT NULL,
  annotation_type TEXT DEFAULT 'note', -- note, question, insight, critique
  page_number INTEGER,
  position JSONB, -- If not tied to highlight
  tags JSONB DEFAULT '[]',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- KNOWLEDGE BASE & CONCEPTS
-- ============================================================================

-- Concepts (extracted or user-defined)
CREATE TABLE concepts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  description TEXT,
  concept_type TEXT DEFAULT 'user_defined', -- user_defined, extracted, auto_generated
  color TEXT DEFAULT '#3B82F6',
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(user_id, name)
);

-- Connections between entities (papers, concepts, annotations)
CREATE TABLE connections (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  source_type TEXT NOT NULL, -- paper, concept, annotation
  source_id UUID NOT NULL,
  target_type TEXT NOT NULL, -- paper, concept, annotation
  target_id UUID NOT NULL,
  connection_type TEXT DEFAULT 'related', -- related, contradicts, supports, extends, cites
  strength FLOAT DEFAULT 1.0, -- Connection strength (0.0 to 1.0)
  description TEXT,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(user_id, source_type, source_id, target_type, target_id)
);

-- Link concepts to papers/annotations
CREATE TABLE concept_links (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  concept_id UUID NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
  entity_type TEXT NOT NULL, -- paper, annotation, highlight
  entity_id UUID NOT NULL,
  relevance_score FLOAT DEFAULT 1.0,
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(user_id, concept_id, entity_type, entity_id)
);

-- ============================================================================
-- KNOWLEDGE CANVAS & VISUALIZATION
-- ============================================================================

-- Visual canvas workspaces
CREATE TABLE canvases (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  description TEXT,
  canvas_data JSONB DEFAULT '{}', -- Complete canvas state (nodes, edges, layout)
  is_public BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Individual canvas items (nodes on the canvas)
CREATE TABLE canvas_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  canvas_id UUID NOT NULL REFERENCES canvases(id) ON DELETE CASCADE,
  item_type TEXT NOT NULL, -- paper, concept, annotation, note, group
  entity_id UUID, -- ID of the linked entity (if any)
  position JSONB NOT NULL, -- {x, y, z}
  size JSONB DEFAULT '{"width": 200, "height": 100}',
  style JSONB DEFAULT '{}', -- Visual styling
  data JSONB DEFAULT '{}', -- Item-specific data
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- CHAT & CONVERSATIONS
-- ============================================================================

-- Chat sessions with documents
CREATE TABLE chat_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  paper_id UUID REFERENCES papers(id) ON DELETE CASCADE, -- Optional: chat with specific paper
  session_name TEXT,
  session_type TEXT DEFAULT 'document', -- document, knowledge_base, general
  context JSONB DEFAULT '{}', -- Session context and settings
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Individual chat messages
CREATE TABLE chat_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
  role TEXT NOT NULL, -- user, assistant, system
  content TEXT NOT NULL,
  message_type TEXT DEFAULT 'text', -- text, citation, insight, question
  sources JSONB DEFAULT '[]', -- Referenced chunks, papers, annotations
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- RESEARCH CHAINS & WORKFLOWS
-- ============================================================================

-- Research workflow chains
CREATE TABLE research_chains (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  description TEXT,
  chain_type TEXT DEFAULT 'research', -- research, literature_review, analysis
  status TEXT DEFAULT 'active', -- active, completed, archived
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Individual events in research chains
CREATE TABLE research_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  chain_id UUID NOT NULL REFERENCES research_chains(id) ON DELETE CASCADE,
  event_type TEXT NOT NULL, -- paper_added, annotation_created, connection_made, insight_recorded
  entity_type TEXT, -- paper, annotation, concept, connection
  entity_id UUID,
  description TEXT,
  event_data JSONB DEFAULT '{}',
  sequence_order INTEGER,
  created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Core entity indexes
CREATE INDEX idx_papers_user_id ON papers(user_id);
CREATE INDEX idx_papers_status ON papers(processing_status);
CREATE INDEX idx_paper_chunks_paper ON paper_chunks(paper_id);
CREATE INDEX idx_paper_chunks_user ON paper_chunks(user_id);

-- Text search indexes
CREATE INDEX idx_paper_chunks_content ON paper_chunks USING gin(to_tsvector('english', content));
CREATE INDEX idx_papers_title ON papers USING gin(to_tsvector('english', title));
CREATE INDEX idx_concepts_name ON concepts USING gin(to_tsvector('english', name));

-- Annotation and highlight indexes
CREATE INDEX idx_highlights_paper ON highlights(paper_id);
CREATE INDEX idx_annotations_paper ON annotations(paper_id);
CREATE INDEX idx_annotations_highlight ON annotations(highlight_id);

-- Knowledge graph indexes
CREATE INDEX idx_connections_source ON connections(source_type, source_id);
CREATE INDEX idx_connections_target ON connections(target_type, target_id);
CREATE INDEX idx_concept_links_concept ON concept_links(concept_id);
CREATE INDEX idx_concept_links_entity ON concept_links(entity_type, entity_id);

-- Canvas and visualization indexes
CREATE INDEX idx_canvas_items_canvas ON canvas_items(canvas_id);
CREATE INDEX idx_canvas_items_user ON canvas_items(user_id);

-- Chat indexes
CREATE INDEX idx_chat_messages_session ON chat_messages(session_id);
CREATE INDEX idx_chat_sessions_user ON chat_sessions(user_id);

-- Research chain indexes
CREATE INDEX idx_research_events_chain ON research_events(chain_id);
CREATE INDEX idx_research_events_sequence ON research_events(sequence_order);

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================

-- Enable RLS on all tables
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE papers ENABLE ROW LEVEL SECURITY;
ALTER TABLE paper_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE highlights ENABLE ROW LEVEL SECURITY;
ALTER TABLE annotations ENABLE ROW LEVEL SECURITY;
ALTER TABLE concepts ENABLE ROW LEVEL SECURITY;
ALTER TABLE connections ENABLE ROW LEVEL SECURITY;
ALTER TABLE concept_links ENABLE ROW LEVEL SECURITY;
ALTER TABLE canvases ENABLE ROW LEVEL SECURITY;
ALTER TABLE canvas_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE research_chains ENABLE ROW LEVEL SECURITY;
ALTER TABLE research_events ENABLE ROW LEVEL SECURITY;

-- RLS Policies (users can only access their own data)
CREATE POLICY "Users can view own profile" ON profiles FOR ALL USING (auth.uid() = id);
-- Profile policy is already covered above
CREATE POLICY "Users can manage own papers" ON papers FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can manage own chunks" ON paper_chunks FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can manage own highlights" ON highlights FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can manage own annotations" ON annotations FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can manage own concepts" ON concepts FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can manage own connections" ON connections FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can manage own concept_links" ON concept_links FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can manage own canvases" ON canvases FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can manage own canvas_items" ON canvas_items FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can manage own chat_sessions" ON chat_sessions FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can manage own chat_messages" ON chat_messages FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can manage own research_chains" ON research_chains FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can manage own research_events" ON research_events FOR ALL USING (auth.uid() = user_id);

-- ============================================================================
-- UTILITY FUNCTIONS
-- ============================================================================

-- Get comprehensive user statistics
CREATE OR REPLACE FUNCTION get_user_stats(p_user_id UUID)
RETURNS JSON AS $$
DECLARE
  result JSON;
BEGIN
  SELECT json_build_object(
    'total_papers', (SELECT COUNT(*) FROM papers WHERE user_id = p_user_id),
    'completed_papers', (SELECT COUNT(*) FROM papers WHERE user_id = p_user_id AND processing_status = 'completed'),
    'total_chunks', (SELECT COUNT(*) FROM paper_chunks WHERE user_id = p_user_id),
    'total_highlights', (SELECT COUNT(*) FROM highlights WHERE user_id = p_user_id),
    'total_annotations', (SELECT COUNT(*) FROM annotations WHERE user_id = p_user_id),
    'total_concepts', (SELECT COUNT(*) FROM concepts WHERE user_id = p_user_id),
    'total_connections', (SELECT COUNT(*) FROM connections WHERE user_id = p_user_id),
    'total_canvases', (SELECT COUNT(*) FROM canvases WHERE user_id = p_user_id),
    'total_chat_sessions', (SELECT COUNT(*) FROM chat_sessions WHERE user_id = p_user_id),
    'total_research_chains', (SELECT COUNT(*) FROM research_chains WHERE user_id = p_user_id)
  ) INTO result;
  
  RETURN result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Search across all user content
CREATE OR REPLACE FUNCTION search_user_content(p_user_id UUID, p_query TEXT)
RETURNS JSON AS $$
DECLARE
  result JSON;
BEGIN
  SELECT json_build_object(
    'papers', (
      SELECT json_agg(json_build_object('id', id, 'title', title, 'type', 'paper'))
      FROM papers 
      WHERE user_id = p_user_id 
      AND (title ILIKE '%' || p_query || '%' OR abstract ILIKE '%' || p_query || '%')
      LIMIT 10
    ),
    'chunks', (
      SELECT json_agg(json_build_object('id', id, 'content', LEFT(content, 200), 'type', 'chunk'))
      FROM paper_chunks 
      WHERE user_id = p_user_id 
      AND content ILIKE '%' || p_query || '%'
      LIMIT 10
    ),
    'annotations', (
      SELECT json_agg(json_build_object('id', id, 'content', content, 'type', 'annotation'))
      FROM annotations 
      WHERE user_id = p_user_id 
      AND content ILIKE '%' || p_query || '%'
      LIMIT 10
    ),
    'concepts', (
      SELECT json_agg(json_build_object('id', id, 'name', name, 'type', 'concept'))
      FROM concepts 
      WHERE user_id = p_user_id 
      AND (name ILIKE '%' || p_query || '%' OR description ILIKE '%' || p_query || '%')
      LIMIT 10
    )
  ) INTO result;
  
  RETURN result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Demo user for testing (insert into profiles, email is already in auth.users)
INSERT INTO profiles (id, full_name) VALUES ('00000000-0000-0000-0000-000000000000', 'Demo User') ON CONFLICT DO NOTHING;

-- ============================================================================
-- KNOWLEDGE BASE MANAGEMENT (NEW - Required by Frontend)
-- ============================================================================

-- Knowledge bases for grouping papers
CREATE TABLE knowledge_bases (
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
CREATE TABLE knowledge_base_papers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  knowledge_base_id UUID NOT NULL REFERENCES knowledge_bases(id) ON DELETE CASCADE,
  paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
  added_at TIMESTAMP DEFAULT NOW(),
  added_by UUID REFERENCES profiles(id),
  UNIQUE(knowledge_base_id, paper_id)
);

-- Knowledge base sharing/collaboration
CREATE TABLE knowledge_base_shares (
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
CREATE TABLE knowledge_base_insights (
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
CREATE TABLE document_chat_messages (
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
CREATE TABLE document_views (
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
CREATE TABLE search_history (
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
CREATE TABLE paper_metrics (
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
CREATE TABLE user_activity (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  activity_type TEXT NOT NULL, -- paper_view, paper_save, annotation_create, etc.
  entity_type TEXT, -- paper, annotation, highlight, knowledge_base
  entity_id UUID,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- ENHANCED INDEXES FOR PERFORMANCE
-- ============================================================================

-- Knowledge base indexes
CREATE INDEX idx_knowledge_bases_user ON knowledge_bases(user_id);
CREATE INDEX idx_knowledge_bases_status ON knowledge_bases(status);
CREATE INDEX idx_knowledge_base_papers_kb ON knowledge_base_papers(knowledge_base_id);
CREATE INDEX idx_knowledge_base_papers_paper ON knowledge_base_papers(paper_id);
CREATE INDEX idx_knowledge_base_shares_kb ON knowledge_base_shares(knowledge_base_id);
CREATE INDEX idx_knowledge_base_shares_user ON knowledge_base_shares(shared_with_user_id);

-- Document and search indexes
CREATE INDEX idx_document_chat_messages_paper ON document_chat_messages(paper_id);
CREATE INDEX idx_document_views_user_paper ON document_views(user_id, paper_id);
CREATE INDEX idx_search_history_user ON search_history(user_id);
CREATE INDEX idx_paper_metrics_quality ON paper_metrics(quality_score);
CREATE INDEX idx_user_activity_user_type ON user_activity(user_id, activity_type);

-- Full-text search indexes
CREATE INDEX idx_knowledge_bases_name ON knowledge_bases USING gin(to_tsvector('english', name));
CREATE INDEX idx_knowledge_bases_description ON knowledge_bases USING gin(to_tsvector('english', description));

-- ============================================================================
-- ENHANCED ROW LEVEL SECURITY
-- ============================================================================

-- Enable RLS on new tables
ALTER TABLE knowledge_bases ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_base_papers ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_base_shares ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_base_insights ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_chat_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_views ENABLE ROW LEVEL SECURITY;
ALTER TABLE search_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE paper_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_activity ENABLE ROW LEVEL SECURITY;

-- RLS Policies for knowledge bases
CREATE POLICY "Users can manage own knowledge bases" ON knowledge_bases FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can view shared knowledge bases" ON knowledge_bases FOR SELECT USING (
  auth.uid() = user_id OR 
  is_public = true OR 
  EXISTS (
    SELECT 1 FROM knowledge_base_shares 
    WHERE knowledge_base_id = knowledge_bases.id 
    AND shared_with_user_id = auth.uid()
  )
);

CREATE POLICY "Users can manage own kb papers" ON knowledge_base_papers FOR ALL USING (
  EXISTS (SELECT 1 FROM knowledge_bases WHERE id = knowledge_base_id AND user_id = auth.uid())
);

CREATE POLICY "Users can manage own kb shares" ON knowledge_base_shares FOR ALL USING (
  auth.uid() = shared_by_user_id OR auth.uid() = shared_with_user_id
);

CREATE POLICY "Users can view kb insights" ON knowledge_base_insights FOR SELECT USING (
  EXISTS (
    SELECT 1 FROM knowledge_bases kb 
    WHERE kb.id = knowledge_base_id 
    AND (kb.user_id = auth.uid() OR kb.is_public = true)
  )
);

-- RLS Policies for document features
CREATE POLICY "Users can manage own document chat" ON document_chat_messages FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can manage own document views" ON document_views FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can manage own search history" ON search_history FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can view paper metrics" ON paper_metrics FOR SELECT USING (true);
CREATE POLICY "Users can manage own activity" ON user_activity FOR ALL USING (auth.uid() = user_id);

-- ============================================================================
-- UTILITY FUNCTIONS FOR FRONTEND SUPPORT
-- ============================================================================

-- Get knowledge base with paper count
CREATE OR REPLACE FUNCTION get_knowledge_base_stats(p_kb_id UUID)
RETURNS JSON AS $$
DECLARE
  result JSON;
BEGIN
  SELECT json_build_object(
    'id', kb.id,
    'name', kb.name,
    'description', kb.description,
    'paper_count', (SELECT COUNT(*) FROM knowledge_base_papers WHERE knowledge_base_id = kb.id),
    'tags', kb.tags,
    'is_public', kb.is_public,
    'status', kb.status,
    'created_at', kb.created_at,
    'updated_at', kb.updated_at
  ) INTO result
  FROM knowledge_bases kb
  WHERE kb.id = p_kb_id;
  
  RETURN result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Enhanced user stats with knowledge bases
CREATE OR REPLACE FUNCTION get_enhanced_user_stats(p_user_id UUID)
RETURNS JSON AS $$
DECLARE
  result JSON;
BEGIN
  SELECT json_build_object(
    'total_papers', (SELECT COUNT(*) FROM papers WHERE user_id = p_user_id),
    'completed_papers', (SELECT COUNT(*) FROM papers WHERE user_id = p_user_id AND processing_status = 'completed'),
    'total_chunks', (SELECT COUNT(*) FROM paper_chunks WHERE user_id = p_user_id),
    'total_highlights', (SELECT COUNT(*) FROM highlights WHERE user_id = p_user_id),
    'total_annotations', (SELECT COUNT(*) FROM annotations WHERE user_id = p_user_id),
    'total_concepts', (SELECT COUNT(*) FROM concepts WHERE user_id = p_user_id),
    'total_connections', (SELECT COUNT(*) FROM connections WHERE user_id = p_user_id),
    'total_canvases', (SELECT COUNT(*) FROM canvases WHERE user_id = p_user_id),
    'total_chat_sessions', (SELECT COUNT(*) FROM chat_sessions WHERE user_id = p_user_id),
    'total_knowledgebases', (SELECT COUNT(*) FROM knowledge_bases WHERE user_id = p_user_id),
    'recent_activity', (
      SELECT json_agg(
        json_build_object(
          'type', activity_type,
          'entity_type', entity_type,
          'entity_id', entity_id,
          'created_at', created_at
        )
      )
      FROM user_activity 
      WHERE user_id = p_user_id 
      ORDER BY created_at DESC 
      LIMIT 10
    )
  ) INTO result;
  
  RETURN result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Get papers with enhanced metadata for frontend
CREATE OR REPLACE FUNCTION get_enhanced_papers(p_user_id UUID, p_limit INTEGER DEFAULT 10)
RETURNS JSON AS $$
DECLARE
  result JSON;
BEGIN
  SELECT json_agg(
    json_build_object(
      'id', p.id,
      'title', p.title,
      'abstract', p.abstract,
      'authors', p.authors,
      'year', p.year,
      'citations', p.citations,
      'institution', p.institution,
      'url', p.pdf_url,
      'topics', p.topics,
      'qualityScore', COALESCE(pm.quality_score, 75),
      'relevanceScore', COALESCE(pm.relevance_score, 80),
      'venue', pm.venue,
      'processing_status', p.processing_status,
      'created_at', p.created_at
    )
  ) INTO result
  FROM papers p
  LEFT JOIN paper_metrics pm ON pm.paper_id = p.id
  WHERE p.user_id = p_user_id
  ORDER BY p.created_at DESC
  LIMIT p_limit;
  
  RETURN result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER; 