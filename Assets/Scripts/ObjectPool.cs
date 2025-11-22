using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using Utilities;

public class ObjectPool : MonoBehaviour
{
    [SerializeField] private GameObject ObjectToPool; // The object template to pool
    [SerializeField] private int AmountToPool = 20; // The initial amount of objects to pool
    
    private static readonly List<GameObject> _pooledObjects = new(); // List to store the pooled objects
    
    /// <summary>
    /// Initializes the object pool by creating a specified number of objects and deactivating them.
    /// </summary>
    private void Start()
    {
        // Deactivate the object template to ensure it's not enabled at instantiation
        ObjectToPool.SetActive(false);
        
        // Spawn the specified amount of objects and add them to the pool
        for (int i = 0; i < AmountToPool; i++)
        {
            SpawnNewEmote();
        }
    }

    // ReSharper disable Unity.PerformanceAnalysis
    /// <summary>
    /// Returns an inactive object from the pool, or creates a new one if all are active.
    /// </summary>
    /// <returns>An inactive GameObject from the pool.</returns>
    public GameObject GetPooledObject()
    {
        // Iterate through the pooled objects
        foreach (GameObject obj in _pooledObjects.Where(obj => !obj.activeInHierarchy))
        {
            // Return the first inactive object found
            return obj;
        }

        // If no inactive object is found, log a warning and create a new object
        Debug.LogWarning("All pooled objects are in use; instantiating a new object.");
        return SpawnNewEmote();
    }
    
    /// <summary>
    /// Creates a new object, adds it to the pool, and returns it.
    /// </summary>
    /// <returns>The newly created GameObject.</returns>
    private GameObject  SpawnNewEmote()
    {
        // Instantiate a new object from the template
        GameObject newObject = Instantiate(ObjectToPool);
        
        // Deactivate the new object
        newObject.SetActive(false);
        
        // Add the new object to the pool
        _pooledObjects.Add(newObject);
        
        // Return the new object
        return newObject;
    }
}
