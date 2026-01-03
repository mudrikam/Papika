---
applyTo: '**'
---

- Use pyside6 as the primary framework for GUI development is mandatory. All GUI components must be implemented using this framework to ensure consistency and compatibility across the application.
- Use the MVC (Model-View-Controller) architectural pattern for organizing code. Separate the data (Model), user interface (View), and control logic (Controller) to enhance maintainability and scalability.
- Adhere to the established coding standards and best practices for pyside6 development. This includes proper naming conventions, code structuring, and documentation to facilitate collaboration and code readability.
- Ise qtawesome for all iconography within the application. Ensure that all icons are sourced from this library to maintain a uniform visual style. Avoid using custom or external icons unless absolutely necessary and approved. Avoid using emojis as icons in the application interface.
- All import statements must be on the top of the file (header), grouped by standard library imports, third-party imports, and local application imports, with a blank line separating each group.
- Excesive try except pass statements are prohibited. All exceptions must be properly handled or logged to ensure that errors are not silently ignored, which can lead to debugging challenges and unstable application behavior.
- Immedietely raise print errors to console instead of using silent fails. This ensures that issues are promptly identified and addressed during development and testing phases.
- Avoid printing error messages on the GUI interface. Instead, use print statements to log errors to the console. This approach helps maintain a clean user interface and allows developers to monitor errors without disrupting the user experience.