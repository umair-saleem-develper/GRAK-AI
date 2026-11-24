-- Run this in your Supabase SQL Editor

-- 1. Create the Users table to store custom tokens
CREATE TABLE public.users (
  id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
  email TEXT NOT NULL,
  tokens INTEGER DEFAULT 10 NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Enable Row Level Security
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

-- Allow users to read their own token balance
CREATE POLICY "Users can view own data" ON public.users
  FOR SELECT USING (auth.uid() = id);

-- 2. Create a Trigger to automatically insert a new user row on sign up
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger AS $$
BEGIN
  INSERT INTO public.users (id, email, tokens)
  VALUES (new.id, new.email, 10);
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();

-- 3. Set up a daily cron job to reset tokens to 10
-- Make sure pg_cron extension is enabled in your Supabase Database Settings
CREATE EXTENSION IF NOT EXISTS pg_cron;

SELECT cron.schedule(
  'reset-daily-tokens',
  '0 0 * * *', -- Runs every day at midnight (UTC)
  $$ UPDATE public.users SET tokens = 10 $$
);
