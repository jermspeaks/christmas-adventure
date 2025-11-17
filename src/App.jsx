import { useState, useEffect } from 'preact/hooks';
import { Header } from './components/Header';
import { Section } from './components/Section';
import { Visualization } from './components/Visualization';

export function App() {
  const [gameData, setGameData] = useState(null);
  const [currentSectionId, setCurrentSectionId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentView, setCurrentView] = useState('game');

  // Handle hash-based routing
  useEffect(() => {
    const updateView = () => {
      const hash = window.location.hash;
      if (hash === '#/visualization') {
        setCurrentView('visualization');
      } else {
        setCurrentView('game');
      }
    };

    updateView();
    window.addEventListener('hashchange', updateView);
    return () => window.removeEventListener('hashchange', updateView);
  }, []);

  useEffect(() => {
    // Load game data from JSON file
    fetch('/game-data.json')
      .then(res => {
        if (!res.ok) {
          throw new Error(`Failed to load game data: ${res.statusText}`);
        }
        return res.json();
      })
      .then(data => {
        setGameData(data.gameData);
        const startingSection = data.startingSection || 'section-1';
        setCurrentSectionId(startingSection);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  const handleChoice = (targetSectionId) => {
    if (gameData && gameData[targetSectionId]) {
      setCurrentSectionId(targetSectionId);
      window.scrollTo(0, 0);
    } else {
      alert('Invalid choice target: ' + targetSectionId);
    }
  };

  const handleReset = () => {
    if (gameData) {
      const startingSection = Object.keys(gameData).includes('section-1') 
        ? 'section-1' 
        : Object.keys(gameData)[0];
      setCurrentSectionId(startingSection);
      window.scrollTo(0, 0);
    }
  };

  if (loading) {
    return (
      <div className="loading">
        <p>Loading adventure...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error">
        <h1>Error</h1>
        <p>{error}</p>
        <p>Make sure you've run the compilation script first.</p>
      </div>
    );
  }

  if (!gameData || !currentSectionId) {
    return (
      <div className="error">
        <h1>Error</h1>
        <p>No game data available.</p>
      </div>
    );
  }

  const currentSection = gameData[currentSectionId];
  if (!currentSection) {
    return (
      <div className="error">
        <h1>Error</h1>
        <p>Section not found: {currentSectionId}</p>
      </div>
    );
  }

  const handleNavigateToVisualization = () => {
    window.location.hash = '#/visualization';
  };

  const handleNavigateToGame = () => {
    window.location.hash = '#/';
  };

  if (currentView === 'visualization') {
    return (
      <>
        <Header 
          onReset={handleReset} 
          currentView={currentView}
          onNavigateToVisualization={handleNavigateToVisualization}
          onNavigateToGame={handleNavigateToGame}
        />
        <Visualization />
      </>
    );
  }

  return (
    <>
      <Header 
        onReset={handleReset} 
        currentView={currentView}
        onNavigateToVisualization={handleNavigateToVisualization}
        onNavigateToGame={handleNavigateToGame}
      />
      <Section 
        section={currentSection} 
        onChoice={handleChoice} 
      />
    </>
  );
}

