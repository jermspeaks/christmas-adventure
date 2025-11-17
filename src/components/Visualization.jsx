import { useState, useEffect, useRef } from 'preact/hooks';

export function Visualization() {
  const [gameData, setGameData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [nodePositions, setNodePositions] = useState(new Map());
  const [connections, setConnections] = useState([]);
  const [svgDimensions, setSvgDimensions] = useState({ width: 800, height: 600 });
  const containerRef = useRef(null);
  const graphRef = useRef(null);
  const nodeRefs = useRef(new Map());
  const animationFrameRef = useRef(null);

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

  if (loading) {
    return (
      <div className="loading">
        <p>Loading visualization...</p>
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

  // Build graph structure
  const sections = Object.values(gameData);
  const sectionMap = new Map(sections.map(s => [s.id, s]));

  // Build edges (connections) from choices
  const buildEdges = () => {
    const edges = [];
    sections.forEach(section => {
      if (section.choices) {
        section.choices.forEach((choice, idx) => {
          if (choice.target && sectionMap.has(choice.target)) {
            edges.push({
              id: `${section.id}-${choice.target}-${idx}`,
              from: section.id,
              to: choice.target,
              choiceIndex: idx,
            });
          }
        });
      }
    });
    return edges;
  };

  const edges = buildEdges();

  // Force-directed graph layout
  useEffect(() => {
    if (!gameData || !graphRef.current) return;

    const width = 2400;
    const height = 1200;
    setSvgDimensions({ width, height });

    // Initialize node positions
    const positions = new Map();
    const velocities = new Map();
    const allSections = Object.values(gameData);
    const startingSectionId = gameData['section-1'] ? 'section-1' : allSections[0]?.id;

    // Initialize positions in a circle or grid
    allSections.forEach((section, index) => {
      const angle = (index / allSections.length) * Math.PI * 2;
      const radius = Math.min(width, height) * 0.3;
      const x = width / 2 + Math.cos(angle) * radius;
      const y = height / 2 + Math.sin(angle) * radius;
      
      positions.set(section.id, { x, y });
      velocities.set(section.id, { x: 0, y: 0 });
    });

    // Place starting node in center
    if (startingSectionId) {
      positions.set(startingSectionId, { x: width / 2, y: height / 2 });
    }

    // Set initial positions immediately so nodes render
    setNodePositions(new Map(positions));

    // Force-directed simulation parameters
    const k = Math.sqrt((width * height) / allSections.length) * 4; // Optimal distance (increased for more spacing)
    const repulsionStrength = k * k * 0.5; // Increased repulsion
    const attractionStrength = 0.003; // Reduced attraction
    const damping = 0.85;
    const iterations = 500; // More iterations for better layout
    let iteration = 0;

    const simulate = () => {
      if (iteration >= iterations) {
        setNodePositions(new Map(positions));
        return;
      }

      // Calculate repulsion forces (all nodes repel each other)
      const forces = new Map();
      allSections.forEach(section => {
        forces.set(section.id, { x: 0, y: 0 });
      });

      allSections.forEach((section1, i) => {
        const pos1 = positions.get(section1.id);
        allSections.slice(i + 1).forEach(section2 => {
          const pos2 = positions.get(section2.id);
          const dx = pos2.x - pos1.x;
          const dy = pos2.y - pos1.y;
          const distance = Math.sqrt(dx * dx + dy * dy) || 1;
          const force = repulsionStrength / (distance * distance);
          const fx = (dx / distance) * force;
          const fy = (dy / distance) * force;

          const force1 = forces.get(section1.id);
          force1.x -= fx;
          force1.y -= fy;
          const force2 = forces.get(section2.id);
          force2.x += fx;
          force2.y += fy;
        });
      });

      // Calculate attraction forces (connected nodes attract)
      edges.forEach(edge => {
        const pos1 = positions.get(edge.from);
        const pos2 = positions.get(edge.to);
        if (!pos1 || !pos2) return;

        const dx = pos2.x - pos1.x;
        const dy = pos2.y - pos1.y;
        const distance = Math.sqrt(dx * dx + dy * dy) || 1;
        const force = (distance / k) * attractionStrength;

        const force1 = forces.get(edge.from);
        force1.x += (dx / distance) * force;
        force1.y += (dy / distance) * force;
        const force2 = forces.get(edge.to);
        force2.x -= (dx / distance) * force;
        force2.y -= (dy / distance) * force;
      });

      // Update velocities and positions
      allSections.forEach(section => {
        const vel = velocities.get(section.id);
        const force = forces.get(section.id);
        
        vel.x = (vel.x + force.x) * damping;
        vel.y = (vel.y + force.y) * damping;
        
        const pos = positions.get(section.id);
        pos.x += vel.x;
        pos.y += vel.y;

        // Keep nodes within bounds
        pos.x = Math.max(50, Math.min(width - 50, pos.x));
        pos.y = Math.max(50, Math.min(height - 50, pos.y));
      });

      // Update positions periodically during simulation for smooth animation
      if (iteration % 10 === 0) {
        setNodePositions(new Map(positions));
      }

      iteration++;
      animationFrameRef.current = requestAnimationFrame(simulate);
    };

    // Start simulation after a brief delay to ensure initial render
    const timeoutId = setTimeout(() => {
      animationFrameRef.current = requestAnimationFrame(simulate);
    }, 100);

    return () => {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [gameData, edges]);

  // Calculate connection paths after positions are set
  useEffect(() => {
    if (nodePositions.size === 0) return;

    const newConnections = [];

    edges.forEach(edge => {
      const fromPos = nodePositions.get(edge.from);
      const toPos = nodePositions.get(edge.to);
      if (!fromPos || !toPos) return;

      // Get actual node dimensions for connection points
      const fromNode = nodeRefs.current.get(edge.from);
      const toNode = nodeRefs.current.get(edge.to);
      if (!fromNode || !toNode) return;

      // Use node dimensions directly (nodes are centered on their positions)
      const fromHeight = fromNode.offsetHeight || 100;
      const toHeight = toNode.offsetHeight || 100;

      // Calculate connection points (bottom of from node, top of to node)
      const fromX = fromPos.x;
      const fromY = fromPos.y + fromHeight / 2;
      const toX = toPos.x;
      const toY = toPos.y - toHeight / 2;

      // Calculate control points for smooth curve
      const dx = toX - fromX;
      const dy = toY - fromY;
      const distance = Math.sqrt(dx * dx + dy * dy);
      const controlOffset = Math.max(30, distance * 0.2);
      const controlY1 = fromY + controlOffset;
      const controlY2 = toY - controlOffset;

      newConnections.push({
        id: edge.id,
        fromX,
        fromY,
        toX,
        toY,
        controlY1,
        controlY2,
      });
    });

    setConnections(newConnections);
  }, [nodePositions, edges]);

  return (
    <div className="visualization-container" ref={containerRef}>
      <h1>Story Path Map</h1>
      <div 
        className="visualization-graph" 
        ref={graphRef}
        style={{ 
          position: 'relative', 
          width: svgDimensions.width, 
          height: svgDimensions.height,
          margin: '0 auto',
          overflow: 'visible'
        }}
      >
        {/* SVG overlay for connections */}
        {svgDimensions.width > 0 && svgDimensions.height > 0 && (
          <svg 
            className="connection-lines" 
            style={{ 
              position: 'absolute', 
              top: 0, 
              left: 0, 
              width: svgDimensions.width, 
              height: svgDimensions.height, 
              pointerEvents: 'none', 
              zIndex: 0,
              overflow: 'visible'
            }}
            viewBox={`0 0 ${svgDimensions.width} ${svgDimensions.height}`}
            preserveAspectRatio="none"
          >
            {connections.map(conn => (
              <path
                key={conn.id}
                d={`M ${conn.fromX} ${conn.fromY} C ${conn.fromX} ${conn.controlY1}, ${conn.toX} ${conn.controlY2}, ${conn.toX} ${conn.toY}`}
                stroke="#c41e3a"
                strokeWidth="2"
                fill="none"
                opacity="0.4"
                markerEnd="url(#arrowhead)"
              />
            ))}
            <defs>
              <marker
                id="arrowhead"
                markerWidth="10"
                markerHeight="10"
                refX="9"
                refY="3"
                orient="auto"
              >
                <polygon points="0 0, 10 3, 0 6" fill="#c41e3a" opacity="0.4" />
              </marker>
            </defs>
          </svg>
        )}

        {/* Graph nodes */}
        <div className="graph-nodes-wrapper" style={{ position: 'relative', zIndex: 1 }}>
          {sections.map(section => {
            const position = nodePositions.get(section.id);
            if (!position) return null;

            return (
              <div
                key={section.id}
                className="graph-node"
                data-section-id={section.id}
                style={{
                  position: 'absolute',
                  left: `${position.x}px`,
                  top: `${position.y}px`,
                  transform: 'translate(-50%, -50%)',
                }}
                ref={el => {
                  if (el) {
                    nodeRefs.current.set(section.id, el);
                  } else {
                    nodeRefs.current.delete(section.id);
                  }
                }}
              >
                <div className="node-content">
                  <h3 className="node-title">{section.title}</h3>
                  {section.choices && section.choices.length > 0 ? (
                    <ul className="node-choices">
                      {section.choices.map((choice, idx) => (
                        <li key={idx} className="node-choice">
                          {choice.text}
                          {choice.target && (
                            <span className="choice-target"> → {sectionMap.get(choice.target)?.title || choice.target}</span>
                          )}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <div className="node-end">The End</div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

