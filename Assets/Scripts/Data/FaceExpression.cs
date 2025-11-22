using System.Collections.Generic;
using Enums;
using Utilities;

namespace Data
{
    public class FaceExpression
    {
        /// <summary>
        /// Gets or sets the timestamp (same as timestamp.png)
        /// </summary>
        public string Timestamp;
     
        /// <summary>
        /// Gets or sets the level ID.
        /// </summary>
        public string LevelID;
     
        /// <summary>
        /// Gets or sets the emote to imitate.
        /// </summary>
        public Emoji Emoji;
     
        /// <summary>
        /// Gets or sets the webcam images.
        /// </summary>
        public string FaceExpressionJson;
    }
}