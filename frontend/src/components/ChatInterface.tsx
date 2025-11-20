import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User } from 'lucide-react'
import { Message, RelevantData } from '../types'
import './ChatInterface.css'

interface ChatInterfaceProps {
  messages: Message[]
  onSendMessage: (content: string) => void | Promise<void>
  isLoading: boolean
  relevantData: RelevantData | null
  onHotelClick?: (hotelId: string) => void
  onTourClick?: (tourId: string) => void
}

export default function ChatInterface({ messages, onSendMessage, isLoading, relevantData, onHotelClick, onTourClick }: ChatInterfaceProps) {
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (input.trim() && !isLoading) {
      onSendMessage(input.trim())
      setInput('')
      if (inputRef.current) {
        inputRef.current.style.height = 'auto'
      }
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value)
    e.target.style.height = 'auto'
    e.target.style.height = `${Math.min(e.target.scrollHeight, 200)}px`
  }

  return (
    <div className="chat-container">
      <div className="chat-header">
        <div className="chat-header-content">
          <div className="chat-header-icon">
            <Bot size={24} />
          </div>
          <div>
            <h1>Rome Itinerary Builder</h1>
            <p>Your personal travel assistant</p>
          </div>
        </div>
      </div>

      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="welcome-message">
            <div className="welcome-icon">
              <Bot size={48} />
            </div>
            <h2>Welcome to Rome!</h2>
            <p>I'm here to help you create the perfect itinerary for your trip to the Eternal City.</p>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`message ${message.role === 'user' ? 'message-user' : 'message-bot'}`}
          >
            <div className="message-avatar">
              {message.role === 'user' ? (
                <User size={20} />
              ) : (
                <Bot size={20} />
              )}
            </div>
            <div className="message-content">
              <div className="message-text">
                {message.content.split('\n').map((line, i) => (
                  <p key={i}>{line}</p>
                ))}
              </div>
              <div className="message-time">
                {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </div>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="message message-bot">
            <div className="message-avatar">
              <Bot size={20} />
            </div>
            <div className="message-content">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}

        {relevantData && (
          <div className="relevant-section">
            <p className="relevant-eyebrow">Related stays & experiences</p>
            {relevantData.hotels.length > 0 && (
              <div className="relevant-group">
                <div className="relevant-group-header">
                  <h3>Hotels you might love</h3>
                  <span>{relevantData.hotels.length} option{relevantData.hotels.length > 1 ? 's' : ''}</span>
                </div>
                <div className="relevant-grid">
                  {relevantData.hotels.map((hotel) => (
                    <article
                      key={hotel.id}
                      className="relevant-card relevant-card-clickable"
                      onClick={() => onHotelClick?.(hotel.id)}
                    >
                      <div className="relevant-card-head">
                        <div>
                          <p className="relevant-card-title">{hotel.name}</p>
                          <p className="relevant-card-meta">
                            {[hotel.city, hotel.country].filter(Boolean).join(', ')}
                          </p>
                        </div>
                      </div>
                      {hotel.description && <p className="relevant-card-description">{hotel.description}</p>}
                      <div className="relevant-card-footer">
                        {hotel.price_range && <span>{hotel.price_range}</span>}
                        <span className="relevant-card-link">View details →</span>
                      </div>
                    </article>
                  ))}
                </div>
              </div>
            )}

            {relevantData.tours.length > 0 && (
              <div className="relevant-group">
                <div className="relevant-group-header">
                  <h3>Featured tours</h3>
                  <span>{relevantData.tours.length} curated</span>
                </div>
                <div className="relevant-grid">
                  {relevantData.tours.map((tour) => (
                    <article
                      key={tour.id}
                      className="relevant-card relevant-card-clickable"
                      onClick={() => onTourClick?.(tour.id)}
                    >
                      <div className="relevant-card-head">
                        <div>
                          <p className="relevant-card-title">{tour.name}</p>
                          <p className="relevant-card-meta">
                            {[tour.city, tour.country].filter(Boolean).join(', ')}
                          </p>
                        </div>
                      </div>
                      {tour.provider && <p className="relevant-card-provider">{tour.provider}</p>}
                      {tour.highlights && tour.highlights.length > 0 && (
                        <ul className="relevant-card-list">
                          {tour.highlights.slice(0, 3).map((highlight, index) => (
                            <li key={`${tour.id}_hl_${index}`}>{highlight}</li>
                          ))}
                        </ul>
                      )}
                      <div className="relevant-card-footer">
                        <span>Guided experience</span>
                        <span className="relevant-card-link">View details →</span>
                      </div>
                    </article>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <form className="chat-input-container" onSubmit={handleSubmit}>
        <div className="chat-input-wrapper">
          <textarea
            ref={inputRef}
            className="chat-input"
            value={input}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder="Tell me about your trip..."
            rows={1}
            disabled={isLoading}
          />
          <button
            type="submit"
            className="chat-send-button"
            disabled={!input.trim() || isLoading}
          >
            <Send size={20} />
          </button>
        </div>
      </form>
    </div>
  )
}

