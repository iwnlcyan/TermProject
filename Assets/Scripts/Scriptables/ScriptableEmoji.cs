using System.Collections.Generic;
using Enums;
using UnityEngine;

namespace Scriptables
{
    public class ScriptableEmoji : ScriptableObject
    {
        public EEmote EEmote;
        public string EnglishName;
        public string GermanName;
        public List<Texture> Textures;
    }
}