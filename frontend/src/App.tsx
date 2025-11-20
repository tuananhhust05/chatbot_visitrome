import { useEffect, useState } from 'react'
import ChatInterface from './components/ChatInterface'
import HotelDetail from './components/HotelDetail'
import TourDetail from './components/TourDetail'
import { Message, RelevantData, RelevantHotel, RelevantTour } from './types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8501/api'
const AGENT_ID = '1'
const DISTANCE_THRESHOLD = 0.65
const CLIENT_ID_STORAGE_KEY = 'visitrome_client_id'

type ApiRelevantHotel = Omit<RelevantHotel, 'metadata'> & {
  metadata?: {
    score?: string | number
    distance?: number | string
  }
}

type ApiRelevantTour = Omit<RelevantTour, 'metadata'> & {
  metadata?: {
    score?: string | number
    distance?: number | string
  }
}

type ApiRelevantData = {
  hotels?: ApiRelevantHotel[]
  tours?: ApiRelevantTour[]
}

const createClientId = () => {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID()
  }
  return `client_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`
}

const persistClientId = (id: string) => {
  try {
    if (typeof window !== 'undefined' && window.localStorage) {
      window.localStorage.setItem(CLIENT_ID_STORAGE_KEY, id)
    }
  } catch (error) {
    console.warn('Unable to persist client id', error)
  }
}

const refreshClientId = () => {
  const newId = createClientId()
  persistClientId(newId)
  return newId
}

type View = 'chat' | 'hotel' | 'tour'

function App() {
  const [view, setView] = useState<View>('chat')
  const [selectedHotelId, setSelectedHotelId] = useState<string>('')
  const [selectedTourId, setSelectedTourId] = useState<string>('')
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [clientId, setClientId] = useState<string>('')
  const [relevantData, setRelevantData] = useState<RelevantData | null>(null)

  useEffect(() => {
    const newClientId = refreshClientId()
    setClientId(newClientId)
  }, [])

  const normalizeDistance = (value: unknown): number => {
    if (typeof value === 'number' && Number.isFinite(value)) return value
    if (typeof value === 'string') {
      const parsed = parseFloat(value)
      if (!Number.isNaN(parsed)) {
        return parsed
      }
    }
    return 1
  }

  const filterRelevantData = (rawData?: ApiRelevantData | null): RelevantData | null => {
    if (!rawData) return null

    const hotels: RelevantHotel[] = (rawData.hotels ?? [])
      .map((hotel) => ({
        ...hotel,
        metadata: {
          ...hotel.metadata,
          distance: normalizeDistance(hotel.metadata?.distance),
        },
      }))
      .filter((hotel) => (hotel.metadata?.distance ?? 1) < DISTANCE_THRESHOLD)

    const tours: RelevantTour[] = (rawData.tours ?? [])
      .map((tour) => ({
        ...tour,
        highlights: tour.highlights?.filter(Boolean),
        metadata: {
          ...tour.metadata,
          distance: normalizeDistance(tour.metadata?.distance),
        },
      }))
      .filter((tour) => (tour.metadata?.distance ?? 1) < DISTANCE_THRESHOLD)

    if (!hotels.length && !tours.length) {
      return null
    }

    return { hotels, tours }
  }

  const handleSendMessage = async (rawContent: string) => {
    const content = rawContent.trim()
    if (!content) return

    let activeClientId = clientId
    if (!activeClientId) {
      activeClientId = refreshClientId()
      setClientId(activeClientId)
    }

    const userMessage: Message = {
      id: `${Date.now()}_${Math.random()}`,
      role: 'user',
      content,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setRelevantData(null)
    setIsLoading(true)

    try {
      const response = await fetch(`${API_BASE_URL}/webhook`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: content,
          client_id: activeClientId,
          agentId: AGENT_ID,
        }),
      })

      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`)
      }

      const data = await response.json()
      const assistantMessage: Message = {
        id: `${Date.now()}_${Math.random()}`,
        role: 'assistant',
        content: (data?.reply ?? '').trim() || "I'm sorry, I couldn't find the information you requested. Please try again.",
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, assistantMessage])
      setRelevantData(filterRelevantData(data?.relevant_data ?? null))
    } catch (error) {
      console.error('Failed to send message:', error)
      const errorMessage: Message = {
        id: `${Date.now()}_${Math.random()}`,
        role: 'assistant',
        content: 'There was a problem contacting our travel concierge. Please try again in a moment.',
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorMessage])
      setRelevantData(null)
    } finally {
      setIsLoading(false)
    }
  }

  const handleHotelClick = (hotelId: string) => {
    setSelectedHotelId(hotelId)
    setView('hotel')
  }

  const handleTourClick = (tourId: string) => {
    setSelectedTourId(tourId)
    setView('tour')
  }

  const handleBackToChat = () => {
    setView('chat')
    setSelectedHotelId('')
    setSelectedTourId('')
  }

  if (view === 'hotel' && selectedHotelId) {
    return (
      <div className="app">
        <HotelDetail hotelId={selectedHotelId} onBack={handleBackToChat} />
      </div>
    )
  }

  if (view === 'tour' && selectedTourId) {
    return (
      <div className="app">
        <TourDetail tourId={selectedTourId} onBack={handleBackToChat} />
      </div>
    )
  }

  return (
    <div className="app">
      <ChatInterface
        messages={messages}
        onSendMessage={handleSendMessage}
        isLoading={isLoading}
        relevantData={relevantData}
        onHotelClick={handleHotelClick}
        onTourClick={handleTourClick}
      />
    </div>
  )
}

export default App

