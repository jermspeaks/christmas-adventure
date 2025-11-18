import { useState, useEffect } from 'preact/hooks';

export function Branches() {
  const [gameData, setGameData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [branches, setBranches] = useState([]);
  const [expandedBranches, setExpandedBranches] = useState(new Set());
  const [expandedSections, setExpandedSections] = useState(new Set());

  useEffect(() => {
    fetch('/game-data.json')
      .then(res => {
        if (!res.ok) {
          throw new Error(`Failed to load game data: ${res.statusText}`);
        }
        return res.json();
      })
      .then(data => {
        setGameData(data.gameData);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  // Check if a section is a terminal ending
  const isTerminalEnding = (sectionId, section) => {
    // Check if choices array is empty
    if (!section.choices || section.choices.length === 0) {
      return true;
    }
    
    // Check if section ID matches terminal ending ranges
    const match = sectionId.match(/^section-(\d+)$/);
    if (match) {
      const num = parseInt(match[1], 10);
      // Terminal ending ranges: 400-499, 500-519, etc.
      if ((num >= 400 && num <= 499) || (num >= 500 && num <= 519)) {
        return true;
      }
    }
    
    return false;
  };

  // Find all paths from starting section to terminal endings using DFS
  const findAllPaths = (gameData, startSectionId) => {
    const paths = [];
    const sectionMap = new Map(Object.entries(gameData));

    const dfs = (currentSectionId, currentPath, currentChoices, visited) => {
      // Avoid infinite loops by checking if we've visited this section in this path
      if (visited.has(currentSectionId)) {
        return;
      }

      const section = sectionMap.get(currentSectionId);
      if (!section) {
        return;
      }

      // Add current section to path
      const newPath = [...currentPath, currentSectionId];
      const newChoices = [...currentChoices];
      const newVisited = new Set(visited);
      newVisited.add(currentSectionId);

      // Check if this is a terminal ending
      if (isTerminalEnding(currentSectionId, section)) {
        paths.push({
          pathId: `path-${paths.length + 1}`,
          sections: newPath,
          choices: newChoices,
        });
        return;
      }

      // Continue exploring choices
      if (section.choices && section.choices.length > 0) {
        section.choices.forEach(choice => {
          if (choice.target && sectionMap.has(choice.target)) {
            dfs(choice.target, newPath, [...newChoices, choice.text], newVisited);
          }
        });
      }
    };

    dfs(startSectionId, [], [], new Set());
    return paths;
  };

  // Generate branches when gameData is loaded
  useEffect(() => {
    if (gameData) {
      const allPaths = findAllPaths(gameData, 'section-1');
      setBranches(allPaths);
      // Expand first branch by default
      if (allPaths.length > 0) {
        setExpandedBranches(new Set([allPaths[0].pathId]));
      }
    }
  }, [gameData]);

  const toggleBranch = (pathId) => {
    const newExpanded = new Set(expandedBranches);
    if (newExpanded.has(pathId)) {
      newExpanded.delete(pathId);
    } else {
      newExpanded.add(pathId);
    }
    setExpandedBranches(newExpanded);
  };

  const toggleSection = (sectionKey) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(sectionKey)) {
      newExpanded.delete(sectionKey);
    } else {
      newExpanded.add(sectionKey);
    }
    setExpandedSections(newExpanded);
  };

  if (loading) {
    return (
      <div className="loading">
        <p>Loading branches...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error">
        <h1>Error</h1>
        <p>{error}</p>
      </div>
    );
  }

  if (!gameData) {
    return (
      <div className="error">
        <h1>Error</h1>
        <p>No game data available.</p>
      </div>
    );
  }

  return (
    <div className="branches-container">
      <h1>Story Branches</h1>
      <p className="branches-intro">
        All complete story paths from section-1 to terminal endings. Use this view to review each branch for continuity errors.
      </p>
      <p className="branches-count">
        Found {branches.length} complete branch{branches.length !== 1 ? 'es' : ''}
      </p>
      
      <div className="branches-list">
        {branches.map((branch, branchIndex) => {
          const isBranchExpanded = expandedBranches.has(branch.pathId);
          
          return (
            <div key={branch.pathId} className="branch-item">
              <div 
                className="branch-header"
                onClick={() => toggleBranch(branch.pathId)}
              >
                <span className="branch-toggle">
                  {isBranchExpanded ? '▼' : '▶'}
                </span>
                <span className="branch-title">
                  Branch {branchIndex + 1} ({branch.sections.length} sections)
                </span>
                <span className="branch-end">
                  Ends at: {branch.sections[branch.sections.length - 1]}
                </span>
              </div>
              
              {isBranchExpanded && (
                <div className="branch-content">
                  {branch.sections.map((sectionId, sectionIndex) => {
                    const section = gameData[sectionId];
                    if (!section) return null;
                    
                    const sectionKey = `${branch.pathId}-${sectionId}`;
                    const isSectionExpanded = expandedSections.has(sectionKey);
                    const choiceText = sectionIndex > 0 ? branch.choices[sectionIndex - 1] : null;
                    
                    return (
                      <div key={sectionKey} className="section-item">
                        <div 
                          className="section-header"
                          onClick={() => toggleSection(sectionKey)}
                        >
                          <span className="section-toggle">
                            {isSectionExpanded ? '▼' : '▶'}
                          </span>
                          <span className="section-id">{sectionId}</span>
                          <span className="section-title">{section.title}</span>
                        </div>
                        
                        {isSectionExpanded && (
                          <div className="section-content">
                            <div className="section-meta">
                              <div className="meta-item">
                                <strong>File:</strong> <code>sections/{sectionId}.md</code>
                              </div>
                              {choiceText && (
                                <div className="meta-item choice-path">
                                  <strong>Choice that led here:</strong> "{choiceText}"
                                </div>
                              )}
                            </div>
                            <div 
                              className="section-body"
                              dangerouslySetInnerHTML={{ __html: section.bodyHtml }}
                            />
                            {section.choices && section.choices.length > 0 && (
                              <div className="section-choices-info">
                                <strong>Choices from this section:</strong>
                                <ul>
                                  {section.choices.map((choice, idx) => (
                                    <li key={idx}>
                                      "{choice.text}" → {choice.target || 'N/A'}
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

