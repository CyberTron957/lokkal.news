import type { Article, Area, Post } from '@prisma/client';

export interface CreateAreaRequest {
  area: string;
  skipCorrection?: boolean;
}

export interface AreaSearchResponse {
  normalizedArea: string;
  correctedArea?: string;
  confidence?: 'high' | 'low';
  created: boolean;
}

export interface CreatePostRequest {
  area: string;
  content: string;
  reporterName?: string;
  image?: string;
}

export interface GenerateNewsRequest {
  area: string;
}

export interface ApiErrorResponse {
  success: false;
  error: string;
}

export interface LikeArticleResponse {
  success: true;
  likes: number;
}

export interface TrendingResponse {
  trendingPages: Array<{ path: string; visits: number; name: string }>;
  trendingArticles: Array<Article & { area: Area | null }>;
}

export interface AreaPageData {
  area: Area;
  articles: Array<Article & { area: Area | null }>;
  posts: Post[];
}
