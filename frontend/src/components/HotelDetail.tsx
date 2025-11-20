import { useEffect, useState } from 'react'
import { ArrowLeft, MapPin, DollarSign, ExternalLink } from 'lucide-react'
import { WeaviateApiResponse, ParsedHotelContent } from '../types'
import './HotelDetail.css'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8501/api'

interface HotelDetailProps {
  hotelId: string
  onBack: () => void
}

export default function HotelDetail({ hotelId, onBack }: HotelDetailProps) {
  const [hotel, setHotel] = useState<ParsedHotelContent | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchHotel = async () => {
      try {
        setLoading(true)
        setError(null)

        const response = await fetch(`${API_BASE_URL}/database/weaviate-data?limit=1000`)
        if (!response.ok) {
          throw new Error(`Failed to fetch: ${response.status}`)
        }

        const data: WeaviateApiResponse = await response.json()
        if (!data.success || !data.data) {
          throw new Error('Invalid response format')
        }

        // Find hotel by ID
        const hotelData = data.data.hotels.find(
          (h) => h.doc_id === hotelId || JSON.parse(h.content || '{}').id === hotelId
        )

        if (!hotelData) {
          throw new Error('Hotel not found')
        }

        // Parse content
        const parsed: ParsedHotelContent = JSON.parse(hotelData.content || '{}')
        setHotel(parsed)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load hotel details')
      } finally {
        setLoading(false)
      }
    }

    fetchHotel()
  }, [hotelId])

  if (loading) {
    return (
      <div className="detail-container">
        <div className="detail-loading">
          <div className="loading-spinner"></div>
          <p>Loading hotel details...</p>
        </div>
      </div>
    )
  }

  if (error || !hotel) {
    return (
      <div className="detail-container">
        <button className="detail-back-button" onClick={onBack}>
          <ArrowLeft size={20} />
          Back
        </button>
        <div className="detail-error">
          <p>{error || 'Hotel not found'}</p>
          <button onClick={onBack} className="detail-error-button">
            Return to chat
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="detail-container">
      <div className="detail-header">
        <button className="detail-back-button" onClick={onBack}>
          <ArrowLeft size={20} />
          Back
        </button>
      </div>

      <div className="detail-content">
        <div className="detail-hero">
          <h1 className="detail-title">{hotel.name}</h1>
          <div className="detail-location">
            <MapPin size={18} />
            <span>
              {[hotel.city, hotel.country].filter(Boolean).join(', ') || 'Location not specified'}
            </span>
          </div>
        </div>

        <div className="detail-sections">
          {hotel.description || hotel.des ? (
            <section className="detail-section">
              <h2 className="detail-section-title">About</h2>
              <p className="detail-section-content">{hotel.description || hotel.des}</p>
            </section>
          ) : null}

          {hotel.price_range && (
            <section className="detail-section">
              <h2 className="detail-section-title">Pricing</h2>
              <div className="detail-price">
                <DollarSign size={20} />
                <span>{hotel.price_range}</span>
              </div>
            </section>
          )}

          <section className="detail-section">
            <h2 className="detail-section-title">Details</h2>
            <div className="detail-info-grid">
              {hotel.id && (
                <div className="detail-info-item">
                  <span className="detail-info-label">ID</span>
                  <span className="detail-info-value">{hotel.id}</span>
                </div>
              )}
              {hotel.city && (
                <div className="detail-info-item">
                  <span className="detail-info-label">City</span>
                  <span className="detail-info-value">{hotel.city}</span>
                </div>
              )}
              {hotel.country && (
                <div className="detail-info-item">
                  <span className="detail-info-label">Country</span>
                  <span className="detail-info-value">{hotel.country}</span>
                </div>
              )}
            </div>
          </section>
        </div>

        <div className="detail-footer">
          <button className="detail-primary-button" onClick={onBack}>
            Return to chat
          </button>
        </div>
      </div>
    </div>
  )
}

