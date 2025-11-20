import { ArrowLeft, Mail, Download, MapPin, Star, Clock, Euro } from 'lucide-react'
import { Itinerary } from '../types'
import './ItineraryDisplay.css'

interface ItineraryDisplayProps {
  itinerary: Itinerary
  onBack: () => void
}

export default function ItineraryDisplay({ itinerary, onBack }: ItineraryDisplayProps) {
  const renderStars = (rating: number) => {
    return Array.from({ length: 5 }).map((_, i) => (
      <Star
        key={i}
        size={14}
        className={i < Math.floor(rating) ? 'star-filled' : 'star-empty'}
        fill={i < Math.floor(rating) ? 'currentColor' : 'none'}
      />
    ))
  }

  return (
    <div className="itinerary-container">
      <div className="itinerary-header">
        <button className="back-button" onClick={onBack}>
          <ArrowLeft size={20} />
        </button>
        <div className="itinerary-header-content">
          <h1>Your Rome Itinerary</h1>
          <p>{itinerary.travelDates.start} - {itinerary.travelDates.end}</p>
        </div>
        <div className="itinerary-actions">
          <button className="action-button">
            <Mail size={18} />
            Email
          </button>
          <button className="action-button">
            <Download size={18} />
            PDF
          </button>
        </div>
      </div>

      <div className="itinerary-content">
        <div className="itinerary-summary">
          <div className="summary-card">
            <div className="summary-label">Travel Dates</div>
            <div className="summary-value">
              {new Date(itinerary.travelDates.start).toLocaleDateString('en-US', { 
                month: 'short', 
                day: 'numeric' 
              })} - {new Date(itinerary.travelDates.end).toLocaleDateString('en-US', { 
                month: 'short', 
                day: 'numeric',
                year: 'numeric'
              })}
            </div>
          </div>
          <div className="summary-card">
            <div className="summary-label">Party Size</div>
            <div className="summary-value">{itinerary.partySize} {itinerary.partySize === 1 ? 'Person' : 'People'}</div>
          </div>
          <div className="summary-card">
            <div className="summary-label">Budget</div>
            <div className="summary-value">{itinerary.budget}</div>
          </div>
        </div>

        <section className="itinerary-section">
          <h2>Where to Stay</h2>
          <div className="recommendations-grid">
            {itinerary.accommodations.map((acc) => (
              <div key={acc.id} className="recommendation-card">
                <div className="card-image">
                  <img src={acc.image} alt={acc.name} />
                  <div className="card-badge">{acc.type}</div>
                </div>
                <div className="card-content">
                  <div className="card-header">
                    <h3>{acc.name}</h3>
                    <div className="card-rating">
                      {renderStars(acc.rating)}
                      <span>{acc.rating}</span>
                    </div>
                  </div>
                  <p className="card-description">{acc.description}</p>
                  <div className="card-footer">
                    <div className="card-location">
                      <MapPin size={14} />
                      <span>{acc.location}</span>
                    </div>
                    <div className="card-price">{acc.price}</div>
                  </div>
                  <a href={acc.link} className="card-link" target="_blank" rel="noopener noreferrer">
                    View Details →
                  </a>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="itinerary-section">
          <h2>Where to Eat</h2>
          <div className="recommendations-grid">
            {itinerary.restaurants.map((rest) => (
              <div key={rest.id} className="recommendation-card">
                <div className="card-image">
                  <img src={rest.image} alt={rest.name} />
                  <div className="card-badge">{rest.cuisine}</div>
                </div>
                <div className="card-content">
                  <div className="card-header">
                    <h3>{rest.name}</h3>
                    <div className="card-rating">
                      {renderStars(rest.rating)}
                      <span>{rest.rating}</span>
                    </div>
                  </div>
                  <p className="card-description">{rest.description}</p>
                  {rest.recommendedDish && (
                    <div className="card-highlight">
                      <strong>Try:</strong> {rest.recommendedDish}
                    </div>
                  )}
                  <div className="card-footer">
                    <div className="card-location">
                      <MapPin size={14} />
                      <span>{rest.location}</span>
                    </div>
                    <div className="card-price">{rest.priceRange}</div>
                  </div>
                  <a href={rest.link} className="card-link" target="_blank" rel="noopener noreferrer">
                    View Details →
                  </a>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="itinerary-section">
          <h2>What to See</h2>
          <div className="recommendations-grid">
            {itinerary.attractions.map((attr) => (
              <div key={attr.id} className="recommendation-card">
                <div className="card-image">
                  <img src={attr.image} alt={attr.name} />
                  <div className="card-badge">{attr.category}</div>
                </div>
                <div className="card-content">
                  <div className="card-header">
                    <h3>{attr.name}</h3>
                    <div className="card-rating">
                      {renderStars(attr.rating)}
                      <span>{attr.rating}</span>
                    </div>
                  </div>
                  <p className="card-description">{attr.description}</p>
                  <div className="card-footer">
                    <div className="card-meta">
                      <div className="card-location">
                        <MapPin size={14} />
                        <span>{attr.location}</span>
                      </div>
                      {attr.duration && (
                        <div className="card-duration">
                          <Clock size={14} />
                          <span>{attr.duration}</span>
                        </div>
                      )}
                    </div>
                    <div className="card-price">{attr.price}</div>
                  </div>
                  <a href={attr.link} className="card-link" target="_blank" rel="noopener noreferrer">
                    Book Tour →
                  </a>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="itinerary-section">
          <h2>What to Do</h2>
          <div className="recommendations-grid">
            {itinerary.activities.map((act) => (
              <div key={act.id} className="recommendation-card">
                <div className="card-image">
                  <img src={act.image} alt={act.name} />
                  <div className="card-badge">{act.type}</div>
                </div>
                <div className="card-content">
                  <div className="card-header">
                    <h3>{act.name}</h3>
                    <div className="card-rating">
                      {renderStars(act.rating)}
                      <span>{act.rating}</span>
                    </div>
                  </div>
                  <p className="card-description">{act.description}</p>
                  <div className="card-footer">
                    <div className="card-meta">
                      <div className="card-duration">
                        <Clock size={14} />
                        <span>{act.duration}</span>
                      </div>
                    </div>
                    <div className="card-price">{act.price}</div>
                  </div>
                  <a href={act.link} className="card-link" target="_blank" rel="noopener noreferrer">
                    Book Activity →
                  </a>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}

