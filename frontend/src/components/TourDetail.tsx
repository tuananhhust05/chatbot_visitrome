import { useEffect, useState } from 'react'
import { ArrowLeft, MapPin, Clock, User, ExternalLink, Navigation } from 'lucide-react'
import { WeaviateApiResponse, ParsedTourContent, ParsedTourItem } from '../types'
import './TourDetail.css'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8501/api'

interface TourDetailProps {
  tourId: string
  onBack: () => void
}

export default function TourDetail({ tourId, onBack }: TourDetailProps) {
  const [tour, setTour] = useState<ParsedTourContent | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchTour = async () => {
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

        // Find tour by ID
        const tourData = data.data.tours.find(
          (t) =>
            t.doc_id === tourId ||
            JSON.parse(t.content || '{}').tour_id === tourId ||
            JSON.parse(t.content || '{}').id === tourId
        )

        if (!tourData) {
          throw new Error('Tour not found')
        }

        // Parse content
        const parsed: ParsedTourContent = JSON.parse(tourData.content || '{}')
        setTour(parsed)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load tour details')
      } finally {
        setLoading(false)
      }
    }

    fetchTour()
  }, [tourId])

  const totalDuration = tour?.items?.reduce((acc, item) => acc + (item.duration_minutes || 0), 0) || 0
  const tourName = tour?.tour_name || tour?.name || 'Tour'

  if (loading) {
    return (
      <div className="detail-container">
        <div className="detail-loading">
          <div className="loading-spinner"></div>
          <p>Loading tour details...</p>
        </div>
      </div>
    )
  }

  if (error || !tour) {
    return (
      <div className="detail-container">
        <button className="detail-back-button" onClick={onBack}>
          <ArrowLeft size={20} />
          Back
        </button>
        <div className="detail-error">
          <p>{error || 'Tour not found'}</p>
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
          <h1 className="detail-title">{tourName}</h1>
          <div className="detail-location">
            <MapPin size={18} />
            <span>
              {[tour.city, tour.country].filter(Boolean).join(', ') || 'Location not specified'}
            </span>
          </div>
          {tour.provider?.name && (
            <div className="detail-provider">
              <User size={16} />
              <span>{tour.provider.name}</span>
            </div>
          )}
        </div>

        {tour.items && tour.items.length > 0 && (
          <section className="tour-roadmap-section">
            <div className="tour-roadmap-header">
              <h2 className="detail-section-title">Itinerary</h2>
              {totalDuration > 0 && (
                <div className="tour-duration-badge">
                  <Clock size={16} />
                  <span>{Math.round(totalDuration / 60)}h {totalDuration % 60}m total</span>
                </div>
              )}
            </div>
            <div className="tour-roadmap">
              {tour.items.map((item: ParsedTourItem, index: number) => (
                <div key={index} className="roadmap-item" style={{ animationDelay: `${index * 0.1}s` }}>
                  <div className="roadmap-connector">
                    <div className="roadmap-dot"></div>
                    {index < tour.items!.length - 1 && <div className="roadmap-line"></div>}
                  </div>
                  <div className="roadmap-content">
                    <div className="roadmap-header">
                      <div className="roadmap-step-number">{index + 1}</div>
                      <h3 className="roadmap-location-name">
                        {item.location_name || `Stop ${index + 1}`}
                      </h3>
                      {item.duration_minutes && (
                        <div className="roadmap-item-duration">
                          <Clock size={14} />
                          <span>{item.duration_minutes}m</span>
                        </div>
                      )}
                    </div>
                    {item.description && (
                      <p className="roadmap-description">{item.description}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        <div className="detail-sections">
          {tour.provider && (
            <section className="detail-section">
              <h2 className="detail-section-title">Provider Information</h2>
              <div className="detail-info-grid">
                {tour.provider.name && (
                  <div className="detail-info-item">
                    <span className="detail-info-label">Provider</span>
                    <span className="detail-info-value">{tour.provider.name}</span>
                  </div>
                )}
                {tour.provider.contact_email && (
                  <div className="detail-info-item">
                    <span className="detail-info-label">Contact</span>
                    <span className="detail-info-value">{tour.provider.contact_email}</span>
                  </div>
                )}
                {tour.provider.website && (
                  <div className="detail-info-item">
                    <span className="detail-info-label">Website</span>
                    <a
                      href={tour.provider.website}
                      target="_blank"
                      rel="noreferrer"
                      className="detail-info-link"
                    >
                      Visit website <ExternalLink size={14} />
                    </a>
                  </div>
                )}
              </div>
            </section>
          )}

          <section className="detail-section">
            <h2 className="detail-section-title">Details</h2>
            <div className="detail-info-grid">
              {(tour.tour_id || tour.id) && (
                <div className="detail-info-item">
                  <span className="detail-info-label">Tour ID</span>
                  <span className="detail-info-value">{tour.tour_id || tour.id}</span>
                </div>
              )}
              {tour.city && (
                <div className="detail-info-item">
                  <span className="detail-info-label">City</span>
                  <span className="detail-info-value">{tour.city}</span>
                </div>
              )}
              {tour.country && (
                <div className="detail-info-item">
                  <span className="detail-info-label">Country</span>
                  <span className="detail-info-value">{tour.country}</span>
                </div>
              )}
              {totalDuration > 0 && (
                <div className="detail-info-item">
                  <span className="detail-info-label">Total Duration</span>
                  <span className="detail-info-value">
                    {Math.round(totalDuration / 60)}h {totalDuration % 60}m
                  </span>
                </div>
              )}
            </div>
          </section>
        </div>

        <div className="detail-footer">
          {tour.provider?.website && (
            <a
              href={tour.provider.website}
              target="_blank"
              rel="noreferrer"
              className="detail-primary-button detail-primary-button-link"
            >
              Book this tour <ExternalLink size={18} />
            </a>
          )}
          <button className="detail-primary-button" onClick={onBack}>
            Return to chat
          </button>
        </div>
      </div>
    </div>
  )
}

