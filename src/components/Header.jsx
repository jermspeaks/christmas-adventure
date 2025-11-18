export function Header({ onReset, currentView, onNavigateToVisualization, onNavigateToGame, onNavigateToBranches }) {
  return (
    <div className="header">
      <h1>Choose Your Own Christmas Adventure</h1>
      <div className="header-actions">
        {currentView === 'game' ? (
          <>
            <button id="reset-btn" onClick={onReset}>
              Start Over
            </button>
            <button id="map-btn" onClick={onNavigateToVisualization}>
              View Map
            </button>
            <button id="branches-btn" onClick={onNavigateToBranches}>
              View Branches
            </button>
          </>
        ) : currentView === 'visualization' ? (
          <>
            <button id="back-btn" onClick={onNavigateToGame}>
              Back to Game
            </button>
            <button id="branches-btn" onClick={onNavigateToBranches}>
              View Branches
            </button>
          </>
        ) : (
          <>
            <button id="back-btn" onClick={onNavigateToGame}>
              Back to Game
            </button>
            <button id="map-btn" onClick={onNavigateToVisualization}>
              View Map
            </button>
          </>
        )}
      </div>
    </div>
  );
}

