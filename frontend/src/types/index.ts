export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

export interface RelevantMetadata {
  score?: string | number
  distance?: number
}

export interface RelevantHotel {
  id: string
  name: string
  city?: string
  country?: string
  price_range?: string
  description?: string
  link?: string
  metadata?: RelevantMetadata
}

export interface RelevantTour {
  id: string
  name: string
  city?: string
  country?: string
  provider?: string
  link?: string
  highlights?: string[]
  metadata?: RelevantMetadata
}

export interface RelevantData {
  hotels: RelevantHotel[]
  tours: RelevantTour[]
}

export interface Itinerary {
  id: string
  destination: string
  travelDates: {
    start: string
    end: string
  }
  partySize: number
  budget: string
  accommodations: Accommodation[]
  restaurants: Restaurant[]
  attractions: Attraction[]
  activities: Activity[]
  createdAt: Date
}

export interface Accommodation {
  id: string
  name: string
  type: string
  description: string
  price: string
  rating: number
  image: string
  link: string
  location: string
}

export interface Restaurant {
  id: string
  name: string
  cuisine: string
  description: string
  priceRange: string
  rating: number
  image: string
  link: string
  location: string
  recommendedDish?: string
}

export interface Attraction {
  id: string
  name: string
  category: string
  description: string
  price: string
  rating: number
  image: string
  link: string
  location: string
  duration?: string
}

export interface Activity {
  id: string
  name: string
  type: string
  description: string
  price: string
  rating: number
  image: string
  link: string
  duration: string
}

// API Response Types
export interface WeaviateHotelData {
  _additional: {
    id: string
  }
  agentId: string
  category: string
  chunk_id: string
  content: string // JSON string
  doc_id: string
  url: string
}

export interface WeaviateTourData {
  _additional: {
    id: string
  }
  agentId: string
  category: string
  chunk_id: string
  content: string // JSON string
  doc_id: string
  url: string
}

export interface WeaviateApiResponse {
  success: boolean
  message: string
  data: {
    hotels_count: number
    tours_count: number
    hotels: WeaviateHotelData[]
    tours: WeaviateTourData[]
  }
}

// Parsed Hotel/Tour Content
export interface ParsedHotelContent {
  id: string
  city?: string
  country?: string
  name: string
  price_range?: string
  des?: string
  description?: string
}

export interface ParsedTourItem {
  location_name?: string
  description?: string
  duration_minutes?: number
}

export interface ParsedTourProvider {
  name?: string
  website?: string
  contact_email?: string
}

export interface ParsedTourContent {
  country?: string
  city?: string
  tour_id?: string
  id?: string
  tour_name?: string
  name?: string
  provider?: ParsedTourProvider
  items?: ParsedTourItem[]
}

