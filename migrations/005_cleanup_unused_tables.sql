-- ============================================================================
-- MIGRATION: Cleanup Unused Tables
-- Version: 005
-- Description: Remove unused tables since frontend isn't connected yet
--              Keep only tables needed for DelphiX with long-context features
-- ============================================================================

-- Drop unused concept/connection tables
DROP TABLE IF EXISTS concept_links CASCADE;
DROP TABLE IF EXISTS connections CASCADE;
DROP TABLE IF EXISTS concepts CASCADE;

-- Drop old canvas tables (replaced by knowledge_canvases)
DROP TABLE IF EXISTS canvas_items CASCADE;
DROP TABLE IF EXISTS canvases CASCADE;

-- Drop research chains (not needed)
DROP TABLE IF EXISTS research_events CASCADE;
DROP TABLE IF EXISTS research_chains CASCADE;

-- Drop old chat tables if using document_chat_messages instead
DROP TABLE IF EXISTS chat_messages CASCADE;
DROP TABLE IF EXISTS chat_sessions CASCADE;

-- DONE: Keeping only what DelphiX needs:
-- papers, paper_chunks, paper_metrics
-- highlights, annotations  
-- knowledge_bases, knowledge_base_papers, knowledge_base_shares
-- knowledge_canvases, paper_connection_analyses, research_insights, intelligent_search_sessions
-- document_chat_messages, document_views
-- profiles, user_activity, search_history 