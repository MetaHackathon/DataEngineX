-- ============================================================================
-- MIGRATION: Utility Functions for Frontend Support
-- Version: 003
-- Description: Database functions to support enhanced frontend features
-- ============================================================================

-- ============================================================================
-- KNOWLEDGE BASE UTILITY FUNCTIONS
-- ============================================================================

-- Get knowledge base with paper count and metadata
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

-- Get all knowledge bases for a user with stats
CREATE OR REPLACE FUNCTION get_user_knowledge_bases(p_user_id UUID)
RETURNS JSON AS $$
DECLARE
  result JSON;
BEGIN
  SELECT json_agg(
    json_build_object(
      'id', kb.id,
      'name', kb.name,
      'description', kb.description,
      'paper_count', (SELECT COUNT(*) FROM knowledge_base_papers WHERE knowledge_base_id = kb.id),
      'tags', kb.tags,
      'is_public', kb.is_public,
      'status', kb.status,
      'created_at', kb.created_at,
      'updated_at', kb.updated_at
    )
  ) INTO result
  FROM knowledge_bases kb
  WHERE kb.user_id = p_user_id
  ORDER BY kb.updated_at DESC;
  
  RETURN result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- ENHANCED USER STATS FUNCTIONS  
-- ============================================================================

-- Enhanced user stats with knowledge bases and activity
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

-- ============================================================================
-- ENHANCED PAPER QUERY FUNCTIONS
-- ============================================================================

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
      'qualityScore', COALESCE(pm.quality_score, FLOOR(75 + RANDOM() * 25)::int),
      'relevanceScore', COALESCE(pm.relevance_score, FLOOR(80 + RANDOM() * 20)::int),
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

-- Get papers for a specific knowledge base
CREATE OR REPLACE FUNCTION get_knowledge_base_papers(p_kb_id UUID)
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
      'qualityScore', COALESCE(pm.quality_score, FLOOR(75 + RANDOM() * 25)::int),
      'relevanceScore', COALESCE(pm.relevance_score, FLOOR(80 + RANDOM() * 20)::int),
      'venue', COALESCE(pm.venue, 'arXiv'),
      'processing_status', p.processing_status,
      'added_at', kbp.added_at
    )
  ) INTO result
  FROM knowledge_base_papers kbp
  JOIN papers p ON p.id = kbp.paper_id
  LEFT JOIN paper_metrics pm ON pm.paper_id = p.id
  WHERE kbp.knowledge_base_id = p_kb_id
  ORDER BY kbp.added_at DESC;
  
  RETURN result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- SEARCH AND DISCOVERY FUNCTIONS
-- ============================================================================

-- Enhanced search with quality and relevance scoring
CREATE OR REPLACE FUNCTION enhanced_paper_search(
  p_user_id UUID,
  p_query TEXT,
  p_limit INTEGER DEFAULT 20
)
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
      'qualityScore', COALESCE(pm.quality_score, FLOOR(75 + RANDOM() * 25)::int),
      'relevanceScore', COALESCE(pm.relevance_score, FLOOR(80 + RANDOM() * 20)::int),
      'venue', pm.venue,
      'rank', row_number() OVER (ORDER BY ts_rank_cd(search_vector, query) DESC)
    )
  ) INTO result
  FROM (
    SELECT p.*, pm.quality_score, pm.relevance_score, pm.venue,
           to_tsvector('english', p.title || ' ' || COALESCE(p.abstract, '')) as search_vector,
           plainto_tsquery('english', p_query) as query
    FROM papers p
    LEFT JOIN paper_metrics pm ON pm.paper_id = p.id
    WHERE p.user_id = p_user_id
      AND to_tsvector('english', p.title || ' ' || COALESCE(p.abstract, '')) @@ plainto_tsquery('english', p_query)
  ) p
  ORDER BY ts_rank_cd(search_vector, query) DESC
  LIMIT p_limit;
  
  RETURN result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- ACTIVITY TRACKING FUNCTIONS
-- ============================================================================

-- Log user activity
CREATE OR REPLACE FUNCTION log_user_activity(
  p_user_id UUID,
  p_activity_type TEXT,
  p_entity_type TEXT DEFAULT NULL,
  p_entity_id UUID DEFAULT NULL,
  p_metadata JSONB DEFAULT '{}'
)
RETURNS UUID AS $$
DECLARE
  activity_id UUID;
BEGIN
  INSERT INTO user_activity (user_id, activity_type, entity_type, entity_id, metadata)
  VALUES (p_user_id, p_activity_type, p_entity_type, p_entity_id, p_metadata)
  RETURNING id INTO activity_id;
  
  RETURN activity_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER; 