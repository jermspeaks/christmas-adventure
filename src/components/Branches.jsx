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
    const MAX_DEPTH = 50; // Prevent infinite loops
    const MAX_PATHS = 100; // Limit total paths to prevent performance issues
    let pathsFound = 0;

    const dfs = (currentSectionId, currentPath, currentChoices, visited, depth = 0) => {
      // Stop if we've found too many paths
      if (pathsFound >= MAX_PATHS) {
        return;
      }

      // Prevent infinite loops and excessive depth
      if (depth > MAX_DEPTH) {
        console.warn(`Path exceeded max depth at ${currentSectionId}`);
        return;
      }

      // Avoid infinite loops by checking if we've visited this section in this path
      if (visited.has(currentSectionId)) {
        return;
      }

      const section = sectionMap.get(currentSectionId);
      if (!section) {
        console.warn(`Section not found: ${currentSectionId}`);
        return;
      }

      // Add current section to path
      const newPath = [...currentPath, currentSectionId];
      const newChoices = [...currentChoices];
      const newVisited = new Set(visited);
      newVisited.add(currentSectionId);

      // Check if this is a terminal ending
      if (isTerminalEnding(currentSectionId, section)) {
        pathsFound++;
        paths.push({
          pathId: `path-${pathsFound}`,
          sections: newPath,
          choices: newChoices,
        });
        return;
      }

      // Continue exploring choices
      if (section.choices && section.choices.length > 0) {
        section.choices.forEach(choice => {
          if (pathsFound >= MAX_PATHS) {
            return;
          }
          if (choice.target) {
            if (sectionMap.has(choice.target)) {
              dfs(choice.target, newPath, [...newChoices, choice.text], newVisited, depth + 1);
            } else {
              console.warn(`Invalid target section: ${choice.target} from ${currentSectionId}`);
            }
          }
        });
      } else {
        // Section has no choices but wasn't detected as terminal - treat it as terminal
        pathsFound++;
        paths.push({
          pathId: `path-${pathsFound}`,
          sections: newPath,
          choices: newChoices,
        });
      }
    };

    if (!sectionMap.has(startSectionId)) {
      console.error(`Starting section not found: ${startSectionId}`);
      return [];
    }

    try {
      dfs(startSectionId, [], [], new Set(), 0);
      console.log(`Found ${paths.length} complete paths from ${startSectionId}`);
    } catch (error) {
      console.error('Error finding paths:', error);
    }
    return paths;
  };

  // Generate branches when gameData is loaded
  useEffect(() => {
    if (gameData) {
      setLoading(true);
      // Use requestAnimationFrame to avoid blocking the UI thread
      const findPathsAsync = () => {
        try {
          console.log('Starting path finding...');
          const startTime = performance.now();
          const allPaths = findAllPaths(gameData, 'section-1');
          const endTime = performance.now();
          console.log(`Path finding completed in ${(endTime - startTime).toFixed(2)}ms`);
          setBranches(allPaths);
          setLoading(false);
          // Expand first branch by default
          if (allPaths.length > 0) {
            setExpandedBranches(new Set([allPaths[0].pathId]));
          } else {
            console.warn('No paths found!');
          }
        } catch (error) {
          console.error('Error generating branches:', error);
          setError(`Error generating branches: ${error.message}`);
          setLoading(false);
        }
      };
      
      // Use requestIdleCallback if available, otherwise use setTimeout
      if (window.requestIdleCallback) {
        requestIdleCallback(findPathsAsync, { timeout: 5000 });
      } else {
        setTimeout(findPathsAsync, 0);
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

  const toggleAllSectionsInBranch = (branch, e) => {
    e.stopPropagation(); // Prevent branch toggle
    const sectionKeys = branch.sections.map(sectionId => `${branch.pathId}-${sectionId}`);
    const allExpanded = sectionKeys.every(key => expandedSections.has(key));
    
    const newExpanded = new Set(expandedSections);
    if (allExpanded) {
      // Collapse all
      sectionKeys.forEach(key => newExpanded.delete(key));
    } else {
      // Expand all
      sectionKeys.forEach(key => newExpanded.add(key));
    }
    setExpandedSections(newExpanded);
  };

  if (loading) {
    return (
      <div className="loading">
        <p>Loading branches... This may take a moment.</p>
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
        {branches.length === 0 && (
          <span style={{color: 'orange', marginLeft: '10px'}}>
            (No paths found - check console for details)
          </span>
        )}
      </p>
      
      {branches.length === 0 ? (
        <div className="error" style={{marginTop: '20px'}}>
          <p>No branches found. This could mean:</p>
          <ul>
            <li>No terminal endings exist in the game data</li>
            <li>All paths are circular (no valid endings)</li>
            <li>Section-1 doesn't exist or has no valid choices</li>
          </ul>
          <p>Check the browser console for detailed error messages.</p>
        </div>
      ) : (
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
                {isBranchExpanded && (
                  <button
                    className="expand-all-button"
                    onClick={(e) => toggleAllSectionsInBranch(branch, e)}
                    style={{
                      marginLeft: 'auto',
                      padding: '6px 14px',
                      fontSize: '12px',
                      cursor: 'pointer',
                      backgroundColor: 'rgba(255, 255, 255, 0.2)',
                      color: 'white',
                      border: '1px solid rgba(255, 255, 255, 0.3)',
                      borderRadius: '4px',
                      fontWeight: '500',
                      transition: 'background-color 0.2s'
                    }}
                    onMouseEnter={(e) => e.target.style.backgroundColor = 'rgba(255, 255, 255, 0.3)'}
                    onMouseLeave={(e) => e.target.style.backgroundColor = 'rgba(255, 255, 255, 0.2)'}
                  >
                    {branch.sections.every(sectionId => 
                      expandedSections.has(`${branch.pathId}-${sectionId}`)
                    ) ? 'Collapse All' : 'Expand All'}
                  </button>
                )}
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
      )}
    </div>
  );
}

