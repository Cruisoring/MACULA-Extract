using System.Runtime.InteropServices;
using System.Text;
using System.Text.Json;
using System.Xml;

Console.OutputEncoding = new UTF8Encoding(false);
var settings = new XmlReaderSettings
{
    DtdProcessing = DtdProcessing.Prohibit,
    XmlResolver = null,
    ValidationType = ValidationType.None,
    ConformanceLevel = ConformanceLevel.Document,
    CheckCharacters = true,
    IgnoreWhitespace = false,
    IgnoreComments = false,
    IgnoreProcessingInstructions = false,
    CloseInput = false
};

void Emit(params object?[] values) =>
    Console.WriteLine(JsonSerializer.Serialize(values));

var text = new StringBuilder();
void FlushText()
{
    if (text.Length > 0)
    {
        Emit("text", text.ToString());
        text.Clear();
    }
}

try
{
    Emit("profile", 1, "System.Xml.XmlReader", RuntimeInformation.FrameworkDescription);
    using var reader = XmlReader.Create(Console.OpenStandardInput(), settings);
    while (reader.Read())
    {
        if (reader.NodeType is XmlNodeType.Text or XmlNodeType.Whitespace or XmlNodeType.SignificantWhitespace)
        {
            text.Append(reader.Value);
            continue;
        }
        FlushText();
        switch (reader.NodeType)
        {
            case XmlNodeType.XmlDeclaration:
                break;
            case XmlNodeType.Element:
                if (reader.NamespaceURI == "http://www.w3.org/2001/XInclude" && reader.LocalName == "include")
                    throw new XmlException("XInclude is not authorized");
                var name = new[] { reader.NamespaceURI, reader.LocalName, reader.Prefix, reader.Name };
                var empty = reader.IsEmptyElement;
                var attributes = new List<string[]>();
                if (reader.MoveToFirstAttribute())
                {
                    do
                    {
                        attributes.Add(new[] {
                            reader.NamespaceURI, reader.LocalName, reader.Prefix, reader.Name, reader.Value
                        });
                    } while (reader.MoveToNextAttribute());
                    reader.MoveToElement();
                }
                var line = (IXmlLineInfo)reader;
                Emit("start", name, attributes, line.LineNumber, line.LinePosition);
                if (empty)
                    Emit("end");
                break;
            case XmlNodeType.EndElement:
                Emit("end");
                break;
            case XmlNodeType.CDATA:
                Emit("cdata", reader.Value);
                break;
            case XmlNodeType.Comment:
                Emit("comment", reader.Value);
                break;
            case XmlNodeType.ProcessingInstruction:
                Emit("pi", reader.Value, reader.Name);
                break;
            default:
                throw new XmlException($"Unsupported authoritative reader event: {reader.NodeType}");
        }
    }
    FlushText();
    Emit("complete");
    return 0;
}
catch (Exception error) when (error is XmlException or IOException)
{
    Console.Error.WriteLine($"Authoritative XmlReader parse FAILED: {error.Message}");
    return 1;
}
