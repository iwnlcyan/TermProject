namespace Enums
{
    /// <summary>
    /// Enumerates types of UI interactions, used to identify and forward UI interactions to the GameManager.
    /// </summary>
    public enum UIType
    {
        /// <summary>
        /// Default state or unspecified UI interaction.
        /// </summary>
        Default,

        /// <summary>
        /// Indicates a request to start the level.
        /// </summary>
        StartLevel,

        /// <summary>
        /// Indicates a request to stop the level.
        /// </summary>
        StopLevel,

        /// <summary>
        /// Indicates a request to pause the level.
        /// </summary>
        PauseLevel,

        /// <summary>
        /// Indicates a request to continue from the end screen.
        /// </summary>
        ContinueEndScreen,

        /// <summary>
        /// Indicates a toggle request to start or stop the level.
        /// </summary>
        StartStopLevel
    }
}