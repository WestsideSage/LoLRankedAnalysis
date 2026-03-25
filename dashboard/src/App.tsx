import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { SearchPage } from './components/search-page';
import { PlayerOverview } from './components/player-overview';
import { RankedView } from './components/ranked-view';
import { AramView } from './components/aram-view';
import { ArenaView } from './components/arena-view';
import { ComparisonView } from './components/comparison-view';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<SearchPage />} />
        <Route path="/player/:name/:tag" element={<PlayerOverview />} />
        <Route path="/player/:name/:tag/ranked" element={<RankedView />} />
        <Route path="/player/:name/:tag/aram" element={<AramView />} />
        <Route path="/player/:name/:tag/mayhem" element={<AramView isMayhem />} />
        <Route path="/player/:name/:tag/arena" element={<ArenaView />} />
        <Route path="/compare" element={<ComparisonView />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
