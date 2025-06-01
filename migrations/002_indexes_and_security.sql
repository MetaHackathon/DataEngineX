-- ============================================================================
-- MIGRATION: Indexes and Row Level Security 
-- Version: 002
-- Description: Performance indexes and security policies for knowledge base tables
-- ============================================================================

-- ============================================================================
-- PERFORMANCE INDEXES
-- ============================================================================

-- Knowledge base indexes
CREATE INDEX IF NOT EXISTS idx_knowledge_bases_user ON knowledge_bases(user_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_bases_status ON knowledge_bases(status);
CREATE INDEX IF NOT EXISTS idx_knowledge_base_papers_kb ON knowledge_base_papers(knowledge_base_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_base_papers_paper ON knowledge_base_papers(paper_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_base_shares_kb ON knowledge_base_shares(knowledge_base_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_base_shares_user ON knowledge_base_shares(shared_with_user_id);

-- Document and search indexes
CREATE INDEX IF NOT EXISTS idx_document_chat_messages_paper ON document_chat_messages(paper_id);
CREATE INDEX IF NOT EXISTS idx_document_views_user_paper ON document_views(user_id, paper_id);
CREATE INDEX IF NOT EXISTS idx_search_history_user ON search_history(user_id);
CREATE INDEX IF NOT EXISTS idx_paper_metrics_quality ON paper_metrics(quality_score);
CREATE INDEX IF NOT EXISTS idx_user_activity_user_type ON user_activity(user_id, activity_type);

-- Full-text search indexes
CREATE INDEX IF NOT EXISTS idx_knowledge_bases_name ON knowledge_bases USING gin(to_tsvector('english', name));
CREATE INDEX IF NOT EXISTS idx_knowledge_bases_description ON knowledge_bases USING gin(to_tsvector('english', description));

-- ============================================================================
-- ROW LEVEL SECURITY SETUP
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

-- ============================================================================
-- ROW LEVEL SECURITY POLICIES
-- ============================================================================

-- Knowledge Base Policies
DROP POLICY IF EXISTS "Users can manage own knowledge bases" ON knowledge_bases;
CREATE POLICY "Users can manage own knowledge bases" ON knowledge_bases FOR ALL USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can view shared knowledge bases" ON knowledge_bases;
CREATE POLICY "Users can view shared knowledge bases" ON knowledge_bases FOR SELECT USING (
  auth.uid() = user_id OR 
  is_public = true OR 
  EXISTS (
    SELECT 1 FROM knowledge_base_shares 
    WHERE knowledge_base_id = knowledge_bases.id 
    AND shared_with_user_id = auth.uid()
  )
);

-- Knowledge Base Papers Policies  
DROP POLICY IF EXISTS "Users can manage own kb papers" ON knowledge_base_papers;
CREATE POLICY "Users can manage own kb papers" ON knowledge_base_papers FOR ALL USING (
  EXISTS (SELECT 1 FROM knowledge_bases WHERE id = knowledge_base_id AND user_id = auth.uid())
);

-- Knowledge Base Sharing Policies
DROP POLICY IF EXISTS "Users can manage own kb shares" ON knowledge_base_shares;
CREATE POLICY "Users can manage own kb shares" ON knowledge_base_shares FOR ALL USING (
  auth.uid() = shared_by_user_id OR auth.uid() = shared_with_user_id
);

-- Knowledge Base Insights Policies
DROP POLICY IF EXISTS "Users can view kb insights" ON knowledge_base_insights;
CREATE POLICY "Users can view kb insights" ON knowledge_base_insights FOR SELECT USING (
  EXISTS (
    SELECT 1 FROM knowledge_bases kb 
    WHERE kb.id = knowledge_base_id 
    AND (kb.user_id = auth.uid() OR kb.is_public = true)
  )
);

-- Document Features Policies
DROP POLICY IF EXISTS "Users can manage own document chat" ON document_chat_messages;
CREATE POLICY "Users can manage own document chat" ON document_chat_messages FOR ALL USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can manage own document views" ON document_views;
CREATE POLICY "Users can manage own document views" ON document_views FOR ALL USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can manage own search history" ON search_history;
CREATE POLICY "Users can manage own search history" ON search_history FOR ALL USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can view paper metrics" ON paper_metrics;
CREATE POLICY "Users can view paper metrics" ON paper_metrics FOR SELECT USING (true);

DROP POLICY IF EXISTS "Users can manage own activity" ON user_activity;
CREATE POLICY "Users can manage own activity" ON user_activity FOR ALL USING (auth.uid() = user_id); 