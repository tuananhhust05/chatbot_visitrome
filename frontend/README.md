# VisitRome Frontend - Custom Itinerary Builder

A beautiful, Apple-inspired chat interface for building custom travel itineraries.

## Features

- 🤖 ChatGPT-like conversational interface
- 🎨 Apple-style design with smooth animations
- 📱 Fully responsive design
- 🏛️ Custom itinerary builder for Rome
- 📧 Email and PDF export functionality (UI ready)
- 🔗 Monetizable links to tours and accommodations

## Tech Stack

- React 18
- TypeScript
- Vite
- Lucide React (icons)
- CSS3 with custom properties

## Getting Started

### Install Dependencies

```bash
npm install
```

### Development

```bash
npm run dev
```

The app will be available at `http://localhost:3000`

### Build

```bash
npm run build
```

### Preview Production Build

```bash
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── ChatInterface.tsx      # Main chat UI component
│   │   ├── ChatInterface.css
│   │   ├── ItineraryDisplay.tsx    # Itinerary results display
│   │   └── ItineraryDisplay.css
│   ├── data/
│   │   └── mockData.ts             # Mock itinerary data
│   ├── types/
│   │   └── index.ts                # TypeScript type definitions
│   ├── App.tsx                     # Main app component
│   ├── main.tsx                    # Entry point
│   └── index.css                   # Global styles
├── index.html
├── package.json
├── tsconfig.json
└── vite.config.ts
```

## Design System

The app uses a custom design system inspired by Apple's design language:

- **Colors**: Clean whites, subtle grays, and Apple blue accent
- **Typography**: System fonts with proper weight hierarchy
- **Spacing**: Consistent 8px grid system
- **Animations**: Smooth, subtle transitions
- **Borders**: Rounded corners (12-24px radius)
- **Shadows**: Soft, layered shadows for depth

## Mock Data

The app includes comprehensive mock data for:
- Accommodations (hotels)
- Restaurants
- Attractions (historical sites, museums)
- Activities (tours, experiences)

All data includes images, ratings, descriptions, and monetizable links.

## Next Steps

1. Connect to OpenAI API for real chat functionality
2. Implement RAG system for personalized recommendations
3. Add email functionality
4. Generate PDF itineraries
5. Integrate booking APIs for monetization

