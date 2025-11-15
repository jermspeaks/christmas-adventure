import { ChoiceButton } from './ChoiceButton';

export function Section({ section, onChoice }) {
  return (
    <div className="section-container">
      <h1>{section.title}</h1>
      <div 
        className="section-body" 
        dangerouslySetInnerHTML={{ __html: section.bodyHtml }} 
      />
      <div className="choices-container">
        {section.choices && section.choices.length > 0 ? (
          <>
            <h2>Your Choices:</h2>
            {section.choices.map((choice, index) => (
              <ChoiceButton
                key={index}
                choice={choice}
                onChoice={onChoice}
              />
            ))}
          </>
        ) : (
          <p><em>The End</em></p>
        )}
      </div>
    </div>
  );
}

