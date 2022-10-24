using Dtos.SessionParameterDtos;

namespace Dtos.SessionDtos {
    public class SessionRelatedParameterDto {
        public SessionRelatedParameterDto(SessionParameterListDto sessionParameterListDto) {
            SessionParameterListDto = sessionParameterListDto;
        }
        public long SessionId { get; set; }
        public string? Name { get; set; }
        public SessionParameterListDto SessionParameterListDto { get; set; }
    }
}