import { Itinerary } from '../types'

export const mockItinerary: Itinerary = {
  id: 'itinerary-001',
  destination: 'Rome, Italy',
  travelDates: {
    start: '2024-06-15',
    end: '2024-06-22'
  },
  partySize: 2,
  budget: 'Mid-range',
  accommodations: [
    {
      id: 'acc-001',
      name: 'Hotel Artemide',
      type: 'Boutique Hotel',
      description: 'Elegant 4-star hotel in the heart of Rome, just steps from Termini Station. Features a rooftop terrace with stunning city views.',
      price: '€150-200/night',
      rating: 4.5,
      image: 'https://images.unsplash.com/photo-1566073771259-6a8506099945?w=800',
      link: '#',
      location: 'Via Nazionale, 22, 00184 Roma'
    },
    {
      id: 'acc-002',
      name: 'The First Roma Dolce',
      type: 'Luxury Hotel',
      description: 'Sophisticated 5-star hotel offering elegant rooms, a spa, and fine dining. Located near the Spanish Steps.',
      price: '€300-400/night',
      rating: 4.8,
      image: 'https://images.unsplash.com/photo-1551882547-ff40c63fe5fa?w=800',
      link: '#',
      location: 'Via del Corso, 126, 00186 Roma'
    }
  ],
  restaurants: [
    {
      id: 'rest-001',
      name: 'Roscioli',
      cuisine: 'Italian, Roman',
      description: 'Iconic Roman trattoria known for exceptional pasta, pizza, and traditional Roman dishes.',
      priceRange: '€€€',
      rating: 4.7,
      image: 'https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=800',
      link: '#',
      location: 'Via dei Giubbonari, 21, 00186 Roma',
      recommendedDish: 'Carbonara, Cacio e Pepe'
    },
    {
      id: 'rest-002',
      name: 'La Pergola',
      cuisine: 'Fine Dining, Mediterranean',
      description: 'Three-Michelin-starred restaurant offering innovative Mediterranean cuisine with panoramic views of Rome.',
      priceRange: '€€€€',
      rating: 4.9,
      image: 'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=800',
      link: '#',
      location: 'Via Alberto Cadlolo, 101, 00136 Roma',
      recommendedDish: 'Tasting Menu'
    },
    {
      id: 'rest-003',
      name: 'Trattoria Da Enzo',
      cuisine: 'Traditional Roman',
      description: 'Charming family-run trattoria in Trastevere serving authentic Roman cuisine in a cozy atmosphere.',
      priceRange: '€€',
      rating: 4.6,
      image: 'https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=800',
      link: '#',
      location: 'Via dei Vascellari, 29, 00153 Roma',
      recommendedDish: 'Amatriciana, Saltimbocca'
    }
  ],
  attractions: [
    {
      id: 'attr-001',
      name: 'Colosseum',
      category: 'Historical Site',
      description: 'The iconic Roman amphitheater, one of the New Seven Wonders of the World. Skip-the-line tickets recommended.',
      price: '€16-24',
      rating: 4.8,
      image: 'https://images.unsplash.com/photo-1552832230-c0197dd311b5?w=800',
      link: '#',
      location: 'Piazza del Colosseo, 1, 00184 Roma',
      duration: '2-3 hours'
    },
    {
      id: 'attr-002',
      name: 'Vatican Museums & Sistine Chapel',
      category: 'Museum, Religious Site',
      description: 'World-renowned art collection including Michelangelo\'s Sistine Chapel ceiling. Early morning or skip-the-line tickets essential.',
      price: '€17-27',
      rating: 4.9,
      image: 'https://images.unsplash.com/photo-1555993537-0e43b8c5c5e3?w=800',
      link: '#',
      location: 'Viale Vaticano, 00165 Roma',
      duration: '3-4 hours'
    },
    {
      id: 'attr-003',
      name: 'Trevi Fountain',
      category: 'Landmark',
      description: 'Baroque masterpiece and one of Rome\'s most famous fountains. Best visited early morning or late evening to avoid crowds.',
      price: 'Free',
      rating: 4.7,
      image: 'https://images.unsplash.com/photo-1529260830199-42c24126f198?w=800',
      link: '#',
      location: 'Piazza di Trevi, 00187 Roma',
      duration: '30 minutes'
    },
    {
      id: 'attr-004',
      name: 'Pantheon',
      category: 'Historical Site',
      description: 'Perfectly preserved Roman temple, now a church, with the world\'s largest unreinforced concrete dome.',
      price: 'Free',
      rating: 4.8,
      image: 'https://images.unsplash.com/photo-1525874684015-58379d421a52?w=800',
      link: '#',
      location: 'Piazza della Rotonda, 00186 Roma',
      duration: '1 hour'
    }
  ],
  activities: [
    {
      id: 'act-001',
      name: 'Rome Food Tour: Trastevere',
      type: 'Food Tour',
      description: 'Explore Trastevere\'s culinary scene with a local guide. Sample authentic Roman dishes, wine, and gelato.',
      price: '€75-95',
      rating: 4.8,
      image: 'https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=800',
      link: '#',
      duration: '3.5 hours'
    },
    {
      id: 'act-002',
      name: 'Vatican Early Access Tour',
      type: 'Guided Tour',
      description: 'Exclusive early morning access to Vatican Museums and Sistine Chapel before general public admission.',
      price: '€89-129',
      rating: 4.9,
      image: 'https://images.unsplash.com/photo-1552832230-c0197dd311b5?w=800',
      link: '#',
      duration: '3 hours'
    },
    {
      id: 'act-003',
      name: 'Vespa Tour of Rome',
      type: 'Adventure Tour',
      description: 'Experience Rome like a local on a vintage Vespa. Visit hidden gems and iconic landmarks with a private guide.',
      price: '€120-180',
      rating: 4.7,
      image: 'https://images.unsplash.com/photo-1558980664-1db506751c6c?w=800',
      link: '#',
      duration: '4 hours'
    },
    {
      id: 'act-004',
      name: 'Cooking Class: Pasta & Tiramisu',
      type: 'Cooking Class',
      description: 'Learn to make fresh pasta and tiramisu from scratch in a traditional Roman kitchen. Includes lunch and wine.',
      price: '€65-85',
      rating: 4.8,
      image: 'https://images.unsplash.com/photo-1556910103-1c02745aae4d?w=800',
      link: '#',
      duration: '3 hours'
    }
  ],
  createdAt: new Date()
}

