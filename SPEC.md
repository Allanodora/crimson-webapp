# TrendStage - Trending Topic Video Generator

## Concept & Vision
A local-first video generation tool that transforms trending topics into engaging video content. The app feels like a professional broadcast control room—dark, focused, with subtle animations that respond to data. It empowers creators to quickly capture trends and render stage-based videos without external services.

## Design Language

### Aesthetic Direction
Broadcast control room meets data visualization dashboard. Dark mode with high-contrast data elements. Think Bloomberg terminal meets Twitch stream overlays.

### Color Palette
- **Background**: `#0a0a0f` (near-black)
- **Surface**: `#16161f` (dark card)
- **Border**: `#2a2a3a` (subtle divider)
- **Primary**: `#6366f1` (indigo accent)
- **Success**: `#22c55e` (green for positive stats)
- **Warning**: `#f59e0b` (amber for attention)
- **Text Primary**: `#f1f5f9`
- **Text Secondary**: `#94a3b8`

### Typography
- **Headings**: `JetBrains Mono` (monospace, tech feel)
- **Body**: `Inter` (clean readability)
- **Data**: `JetBrains Mono` (numbers, stats)

### Motion Philosophy
- Smooth 300ms transitions for state changes
- Pulse animations on live/active elements
- Spring easing for attention-guiding animations

## Layout & Structure

### Web App Layout
```
┌─────────────────────────────────────────────────────┐
│  Header: TrendStage logo + Recording status         │
├──────────────────────┬──────────────────────────────┤
│                      │                              │
│   Graph Panel        │    Preview/Clip Panel         │
│   (Stage Zones)      │    (Live render preview)     │
│                      │                              │
├──────────────────────┴──────────────────────────────┤
│   Comments/Ticker Panel                             │
├─────────────────────────────────────────────────────┤
│   Controls: Record | Stop | Export | Topic Select   │
└─────────────────────────────────────────────────────┘
```

### CLI Layout
```
trendstage --topic "AI trends" --duration 60 --output video.mp4
```

## Features & Interactions

### 1. Trending Topic Collection
- Input: Search query or manual topic entry
- Sources: Twitter/X API, Reddit API, Google Trends (mock data for MVP)
- Display: Topic cards with engagement metrics

### 2. Data Extraction
- **Event**: What happened (parsed from topic title)
- **Stats**: View count, engagement rate, growth velocity
- **Reactions**: Sentiment breakdown, top comments

### 3. Primitive Mapping
| Data | Visual Primitive | Stage Zone |
|------|------------------|------------|
| position | stage zones | Graph panel grid |
| size | focus/scale | Clip panel elements |
| opacity | attention | All panel overlays |
| color | highlight | Accent indicators |
| motion | transitions | Animation triggers |

### 4. Stage Rendering
- **Left (Graph)**: Real-time data visualization, zone-based positioning
- **Right (Clip)**: Preview canvas with composited elements
- **Bottom (Comments)**: Scrolling ticker or stacked cards

### 5. Recording Controls
- Visual variable changes (NOT screen capture):
  - Opacity transitions for attention
  - Scale/pulse for focus
  - Color shifts for highlights
  - Position tweening for stage zones
- Guide attention via spotlight effect

### 6. Export
- Output: MP4 video file
- Resolution: 1080p default
- Frame rate: 30fps

## Component Inventory

### TopicCard
- States: loading, loaded, selected, error
- Shows: title, source, engagement score, trend direction

### GraphPanel
- Grid-based stage zones (3x3 default)
- Active zone highlight with pulse
- Data points as floating nodes

### ClipPreview
- Canvas-based rendering
- Layered compositing (background → data → overlay)

### CommentsTicker
- Horizontal scroll for live ticker
- Vertical stack for full view
- Sentiment-colored backgrounds

### ControlBar
- Record button: red dot when active, pulsing
- Stop: square icon
- Export: download icon
- Topic selector: dropdown with search

## Technical Approach

### Web App
- **Framework**: Vanilla JS + HTML Canvas (no heavy dependencies)
- **Build**: Single HTML file with embedded CSS/JS for portability
- **Storage**: localStorage for preferences

### CLI
- **Language**: Python 3
- **Video**: moviepy for rendering
- **Data**: requests for API calls

### Data Flow
```
Topic Input → API Fetch → Parse → Map Primitives → Render Frame → Encode → Video
```
