function createCircularText(text, recursionLevel, cssParams, parentElement = document.body) {
    if (recursionLevel <= 0) return;

    // Get current CSS parameters for this recursion level
    const currentCSS = cssParams[cssParams.length - recursionLevel] || {};

    // Create the container for the circular text
    const container = document.createElement('div');
    container.classList.add('circular-text-container');
    container.style.position = 'relative';
    container.style.width = currentCSS.diameter || '200px';
    container.style.height = currentCSS.diameter || '200px';
    container.style.display = 'flex';
    container.style.justifyContent = 'center';
    container.style.alignItems = 'center';
    container.style.borderRadius = '50%';
    container.style.overflow = 'hidden';

    // Apply additional CSS parameters to the container
    for (let prop in currentCSS.containerCSS) {
        container.style[prop] = currentCSS.containerCSS[prop];
    }

    parentElement.appendChild(container);

    const radius = parseInt(currentCSS.diameter) / 2 || 100;
    const fontSize = currentCSS.fontSize || '16px';
    const textColor = currentCSS.color || '#000';

    // Position each character around the circle
    for (let i = 0; i < text.length; i++) {
        const charElement = document.createElement('span');
        charElement.innerText = text[i];
        charElement.style.position = 'absolute';
        charElement.style.transformOrigin = `0 ${radius}px`;
        charElement.style.fontSize = fontSize;
        charElement.style.color = textColor;

        // Apply additional CSS parameters to each character
        if (currentCSS.charCSS) {
            for (let prop in currentCSS.charCSS) {
                charElement.style[prop] = currentCSS.charCSS[prop];
            }
        }

        const angle = (360 / text.length) * i;
        charElement.style.transform = `rotate(${angle}deg)`;

        container.appendChild(charElement);
    }

    // Recursive call for the next level
    createCircularText(text, recursionLevel - 1, cssParams, container);
}


const text = "Hello, World!";
const recursionLevel = 3;
const cssParams = [
    {
        diameter: '300px',
        fontSize: '24px',
        color: 'red',
        containerCSS: {
            border: '2px solid red',
        },
        charCSS: {
            fontWeight: 'bold',
        },
    },
    {
        diameter: '200px',
        fontSize: '18px',
        color: 'green',
        containerCSS: {
            border: '2px solid green',
        },
    },
    {
        diameter: '100px',
        fontSize: '12px',
        color: 'blue',
        containerCSS: {
            border: '2px solid blue',
        },
    },
];

createCircularText(text, recursionLevel, cssParams);
