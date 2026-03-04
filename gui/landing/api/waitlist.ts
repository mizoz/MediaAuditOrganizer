/**
 * Waitlist API Endpoint — Mock Implementation
 * 
 * This is a placeholder for the actual waitlist backend.
 * Replace with real implementation when ready.
 * 
 * TODO: Connect to actual backend (Supabase, Firebase, custom API)
 */

interface WaitlistRequest {
  email: string;
  timestamp?: string;
  source?: string;
}

interface WaitlistResponse {
  success: boolean;
  message: string;
  data?: {
    email: string;
    subscribedAt: string;
    status: 'pending' | 'confirmed' | 'alpha';
  };
  error?: string;
}

/**
 * Mock waitlist submission handler
 * Simulates API delay and returns success response
 */
export async function submitWaitlist(
  request: WaitlistRequest
): Promise<WaitlistResponse> {
  // Simulate network delay
  await new Promise((resolve) => setTimeout(resolve, 800));

  // Validate email format
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(request.email)) {
    return {
      success: false,
      message: 'Invalid email address',
      error: 'EMAIL_INVALID',
    };
  }

  // Mock successful submission
  // In production, this would:
  // 1. Check if email already exists in database
  // 2. Insert new record if not exists
  // 3. Send confirmation email
  // 4. Return success response

  console.log('[Mock Waitlist API] Submission:', {
    email: request.email,
    timestamp: request.timestamp || new Date().toISOString(),
    source: request.source || 'landing-page',
  });

  return {
    success: true,
    message: 'Successfully joined waitlist',
    data: {
      email: request.email,
      subscribedAt: new Date().toISOString(),
      status: 'pending',
    },
  };
}

/**
 * Next.js API Route Handler (app/api/waitlist/route.ts)
 * 
 * Uncomment and use when deploying with Next.js
 */
/*
import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { email, source } = body as WaitlistRequest;

    const result = await submitWaitlist({
      email,
      timestamp: new Date().toISOString(),
      source: source || 'landing-page',
    });

    if (!result.success) {
      return NextResponse.json(result, { status: 400 });
    }

    return NextResponse.json(result, { status: 200 });
  } catch (error) {
    console.error('[Waitlist API] Error:', error);
    return NextResponse.json(
      {
        success: false,
        message: 'Internal server error',
        error: 'INTERNAL_ERROR',
      },
      { status: 500 }
    );
  }
}
*/

/**
 * Express.js Route Handler
 * 
 * Uncomment and use when deploying with Express
 */
/*
import { Request, Response } from 'express';

export async function handleWaitlistSubmit(req: Request, res: Response) {
  try {
    const { email, source } = req.body as WaitlistRequest;

    const result = await submitWaitlist({
      email,
      timestamp: new Date().toISOString(),
      source: source || 'landing-page',
    });

    if (!result.success) {
      return res.status(400).json(result);
    }

    return res.status(200).json(result);
  } catch (error) {
    console.error('[Waitlist API] Error:', error);
    return res.status(500).json({
      success: false,
      message: 'Internal server error',
      error: 'INTERNAL_ERROR',
    });
  }
}
*/

/**
 * Vercel Serverless Function
 * 
 * Create file: api/waitlist.ts (Vercel project root)
 */
/*
import type { VercelRequest, VercelResponse } from '@vercel/node';

export default async function handler(req: VercelRequest, res: VercelResponse) {
  // CORS headers
  res.setHeader('Access-Control-Allow-Credentials', 'true');
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  // Handle preflight
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  // Only allow POST
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { email, source } = req.body as WaitlistRequest;

    const result = await submitWaitlist({
      email,
      timestamp: new Date().toISOString(),
      source: source || 'landing-page',
    });

    if (!result.success) {
      return res.status(400).json(result);
    }

    return res.status(200).json(result);
  } catch (error) {
    console.error('[Waitlist API] Error:', error);
    return res.status(500).json({
      success: false,
      message: 'Internal server error',
      error: 'INTERNAL_ERROR',
    });
  }
}
*/

export default submitWaitlist;
