-- Create knowledge_base_analysis table
CREATE TABLE IF NOT EXISTS knowledge_base_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    knowledge_base_id UUID NOT NULL REFERENCES knowledge_bases(id) ON DELETE CASCADE,
    connections JSONB DEFAULT '{}',
    insights JSONB DEFAULT '{}',
    analytics JSONB DEFAULT '{}',
    generated_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(knowledge_base_id)
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_knowledge_base_analysis_kb_id ON knowledge_base_analysis(knowledge_base_id);

-- Add RLS policies
ALTER TABLE knowledge_base_analysis ENABLE ROW LEVEL SECURITY;

-- Policy to allow users to read analysis for their own knowledge bases
CREATE POLICY "Users can read analysis for their own knowledge bases" ON knowledge_base_analysis
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM knowledge_bases 
            WHERE knowledge_bases.id = knowledge_base_analysis.knowledge_base_id 
            AND knowledge_bases.user_id = auth.uid()
        )
    );

-- Policy to allow users to insert/update analysis for their own knowledge bases  
CREATE POLICY "Users can create/update analysis for their own knowledge bases" ON knowledge_base_analysis
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM knowledge_bases 
            WHERE knowledge_bases.id = knowledge_base_analysis.knowledge_base_id 
            AND knowledge_bases.user_id = auth.uid()
        )
    ); 