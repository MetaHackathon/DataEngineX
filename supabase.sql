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